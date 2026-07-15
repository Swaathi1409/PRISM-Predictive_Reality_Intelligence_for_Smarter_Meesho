"""
prism_service.py — Orchestration service for PRISM.

WHAT CHANGED FROM v1:
- detect_event() now returns the full LLM-parsed context dict (not just event_key)
- build_context_bundle() constructs a rich context object from parsed event + Bharat JSON
- context_bundle is passed into every agent call (not just Soch)
- Product matcher receives cultural context to filter appropriately
- match_or_generate() ensures a product card ALWAYS renders
"""

import uuid
import json
from sqlalchemy.orm import Session
from app.models.schemas import PrismRequest, PrismResponse
from app.models.orm_models import Session as SessionModel, Recommendation, AgentLog
from app.engines.life_event_engine import LifeEventEngine
from app.engines.emotional_layer import EmotionalLayer
from app.engines.temporal_simulator import TemporalSimulator
from app.engines.confidence_genome import ConfidenceGenome
from app.engines.product_matcher import match_or_generate
from app.agents.kismat import KismatTrustAgent
from app.agents.paisa import PaisaBudgetAgent
from app.agents.samay import SamayTimeAgent
from app.agents.soch import SochOrchestrator
from app.utils.cache import cache_key, get_cached, set_cached
from app.utils.logger import get_logger
from app.config import settings

logger = get_logger(__name__)


class PrismService:

    def __init__(self, db: Session):
        self.db = db
        self.life_event_engine = LifeEventEngine()
        self.emotional_layer = EmotionalLayer()
        self.temporal_simulator = TemporalSimulator()
        self.confidence_genome = ConfidenceGenome()
        self.kismat = KismatTrustAgent()
        self.paisa = PaisaBudgetAgent()
        self.samay = SamayTimeAgent()
        self.soch = SochOrchestrator()

    async def analyze(self, request: PrismRequest) -> PrismResponse:
        session_id = str(uuid.uuid4())

        # Cache check
        ck = cache_key(request.user_input, request.user_pincode or "", str(request.budget or ""))
        cached = get_cached(ck)
        if cached and settings.environment != "development":
            logger.info(f"Cache hit for session {session_id}")
            return PrismResponse(**cached)

        # ── STEP 1: LLM semantic parse (replaces keyword scan) ──────────────────
        logger.info("Step 1: LLM semantic parse")
        parsed_event = self.life_event_engine.detect_event(request.user_input)
        event_key = parsed_event.get("event_key", "general")
        logger.info(f"Detected event: {event_key} (confidence: {parsed_event.get('confidence', 0):.2f})")

        # ── STEP 2: Build Bharat context bundle ──────────────────────────────────
        logger.info("Step 2: Building Bharat context bundle")
        state = parsed_event.get("detected_state")
        bharat_ctx = self.life_event_engine.get_bharat_context(state)
        institution_name = parsed_event.get("institution_mentioned")
        institution_data = self.life_event_engine.get_institution_data(institution_name)

        # Detect upcoming PM Kisan or salary payment from bharat_context.json
        from datetime import datetime
        current_month = datetime.now().month
        upcoming_payment = _detect_upcoming_payment(bharat_ctx, current_month)

        context_bundle = {
            # From LLM parser
            "event_key": event_key,
            "detected_state": state,
            "detected_location": parsed_event.get("detected_location"),
            "season": parsed_event.get("season"),
            "cultural_context": parsed_event.get("cultural_context", []),
            "travel_purpose": parsed_event.get("travel_purpose"),
            "urgency_days": parsed_event.get("urgency_days") or request.urgency_days,
            "budget": parsed_event.get("budget_mentioned") or request.budget,
            "emotion_level": parsed_event.get("emotion_level", "medium"),
            "family_significance": parsed_event.get("family_significance"),
            "institution_mentioned": institution_name,
            # From Bharat context JSON
            "climate": bharat_ctx.get("climate"),
            "festivals_upcoming": bharat_ctx.get("festivals", []),
            "regional_preferences": bharat_ctx.get("regional_preferences", {}),
            "hard_water": bharat_ctx.get("hard_water", False),
            "institution_data": institution_data,
            "upcoming_scheme_payment": upcoming_payment,
            # From request
            "user_pincode": request.user_pincode or "600001",
        }

        # ── STEP 3: Generate emotional opening ───────────────────────────────────
        logger.info("Step 3: Emotional opening")
        emotional_message = self.emotional_layer.generate_opening(request.user_input, context_bundle)

        # ── STEP 4: Purchase timeline ─────────────────────────────────────────────
        logger.info("Step 4: Purchase timeline")
        template = self.life_event_engine.get_template(event_key)
        timeline = self.life_event_engine.enrich_timeline(template, bharat_ctx, institution_data)
        roadmap_intro = self.life_event_engine.generate_roadmap_intro(parsed_event)

        # ── STEP 5: Product matching with cultural context + fallback ────────────
        logger.info("Step 5: Product matching")
        products = match_or_generate(
            event_key=event_key,
            context_bundle=context_bundle,
            budget=context_bundle["budget"],
            pincode=context_bundle["user_pincode"],
            institution_data=institution_data,
            limit=5
        )

        if not products:
            logger.warning("No products returned even from fallback — using hardcoded placeholder")
            products = [_emergency_placeholder(event_key, context_bundle)]

        top_product = products[0]

        # ── STEP 6: Agent debate ─────────────────────────────────────────────────
        logger.info("Step 6: Agent debate")
        kismat_result = self.kismat.evaluate(top_product, context_bundle)
        paisa_result = self.paisa.evaluate(top_product, context_bundle)
        samay_result = self.samay.evaluate(top_product, context_bundle)
        soch_result = self.soch.deliberate(
            agent_results=[kismat_result, paisa_result, samay_result],
            product=top_product,
            context=context_bundle
        )

        agent_results = [kismat_result, paisa_result, samay_result]

        # ── STEP 7: Confidence genome ─────────────────────────────────────────────
        logger.info("Step 7: Confidence genome")
        confidence = self.confidence_genome.compute(
            agent_results=agent_results,
            soch_score=soch_result["final_score"],
            product=top_product,
            context=context_bundle
        )

        # ── STEP 8: Temporal strategies ───────────────────────────────────────────
        logger.info("Step 8: Temporal strategies")
        temporal = self.temporal_simulator.generate(
            product=top_product,
            context=context_bundle
        )

        # ── STEP 9: Build response ────────────────────────────────────────────────
        response = PrismResponse(
            session_id=session_id,
            detected_event=template.get("label", event_key),
            event_key=event_key,
            emotion_level=context_bundle["emotion_level"],
            family_significance=context_bundle.get("family_significance"),
            emotional_message=emotional_message,
            roadmap_intro=roadmap_intro,
            purchase_timeline=timeline,
            agent_debate=[kismat_result, paisa_result, samay_result, soch_result],
            top_recommendation=top_product,
            all_candidates=products,
            confidence=confidence,
            temporal_strategies=temporal,
            bharat_context={
                "state": state,
                "climate": context_bundle.get("climate"),
                "festivals": context_bundle.get("festivals_upcoming", []),
                "institution": institution_name,
                "institution_constraints": institution_data,
                "cultural_context": context_bundle.get("cultural_context", []),
                "regional_preferences": context_bundle.get("regional_preferences", {})
            },
            state_detected=state,
            institution_detected=institution_name
        )

        # ── STEP 10: Persist and cache ────────────────────────────────────────────
        _save_to_db(self.db, session_id, request, parsed_event, top_product, soch_result, confidence, temporal, emotional_message, agent_results)
        set_cached(ck, response.model_dump())

        return response


def _detect_upcoming_payment(bharat_ctx: dict, current_month: int) -> str | None:
    """
    Checks if a PM Kisan or similar government scheme payment is due in the next 30 days.
    Payment months: April (4), August (8), December (12).
    Returns a descriptive string like "in 12 days" or None.
    """
    from datetime import datetime, timedelta
    pm_kisan_months = bharat_ctx.get("government_schemes", {}).get("pm_kisan", {}).get("payment_months", [4, 8, 12])
    today = datetime.now()
    for month in pm_kisan_months:
        target = today.replace(month=month, day=1)
        if target < today:
            # Try next year
            target = target.replace(year=today.year + 1)
        diff = (target - today).days
        if 0 <= diff <= 30:
            return f"in ~{diff} days"
    return None


def _emergency_placeholder(event_key: str, context: dict) -> dict:
    """Last-resort placeholder when product matcher and LLM fallback both fail."""
    return {
        "id": "placeholder_emergency",
        "name": f"Essential item for {event_key.replace('_', ' ')}",
        "category": "general",
        "price": 0,
        "seller_name": "Pending",
        "seller_rating": 0,
        "seller_review_count": 0,
        "seller_return_rate": 0,
        "delivery_days": 5,
        "available_pincodes": [],
        "stock_status": "out_of_stock",
        "price_trend_7d": 0,
        "tags": [],
        "is_placeholder": True,
        "placeholder_reason": "no_match",
        "why_needed": "This item type is not yet in our catalogue."
    }


def _save_to_db(db, session_id, request, parsed_event, top_product, soch_result, confidence, temporal, emotional_message, agent_results):
    """Saves session, recommendation, and agent logs to the database."""
    try:
        import uuid as _uuid
        session_row = SessionModel(
            id=session_id,
            user_input=request.user_input,
            detected_event=parsed_event.get("event_key", "general"),
            event_key=parsed_event.get("event_key", "general"),
            emotion_level=parsed_event.get("emotion_level", "medium"),
            family_significance=parsed_event.get("family_significance"),
            state_detected=parsed_event.get("detected_state"),
            institution_detected=parsed_event.get("institution_mentioned"),
            user_pincode=request.user_pincode,
            budget=parsed_event.get("budget_mentioned") or request.budget
        )
        db.add(session_row)

        rec_row = Recommendation(
            id=str(_uuid.uuid4()),
            session_id=session_id,
            product_id=top_product.get("id", "unknown"),
            product_name=top_product.get("name", "unknown"),
            final_verdict=soch_result.get("verdict", "unknown"),
            confidence_score=confidence.get("score", 0),
            confidence_breakdown=confidence.get("factors", []),
            temporal_strategies=[t if isinstance(t, dict) else t.model_dump() for t in temporal],
            emotional_message=emotional_message,
            soch_reasoning=soch_result.get("message", "")
        )
        db.add(rec_row)

        for agent_result in agent_results:
            log_row = AgentLog(
                session_id=session_id,
                agent_name=agent_result.get("agent_name", ""),
                agent_role=agent_result.get("agent_role", ""),
                verdict=agent_result.get("verdict", ""),
                message=agent_result.get("message", ""),
                score_contribution=agent_result.get("score_contribution", 0),
                input_snapshot=agent_result.get("data", {})
            )
            db.add(log_row)

        db.commit()
    except Exception as e:
        db.rollback()
        # Log but do not crash — DB failure should not break the response
        import logging
        logging.getLogger(__name__).error(f"DB save failed: {e}")
