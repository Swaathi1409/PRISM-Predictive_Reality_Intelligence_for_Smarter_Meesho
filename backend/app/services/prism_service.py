"""
prism_service.py — Master orchestration service for PRISM.

WHY A SERVICE LAYER:
Route handlers should contain NO business logic — only HTTP concerns.
This service is the single place where all engines and agents are called
in sequence. It can be tested independently of HTTP, imported by tests,
or called by background workers.

ORCHESTRATION ORDER:
1. Check Redis cache (return immediately if cached result found)
2. LifeEventEngine: detect event + location
3. EmotionalLayer: generate warm opening message (LLM call 1)
4. ProductMatcher: filter top 5 candidates
5. Kismat, Paisa, Samay: evaluate top product (deterministic)
6. SochOrchestrator: synthesise and deliberate (LLM call 2)
7. ConfidenceGenome: decompose score into factors
8. TemporalSimulator: generate 3 timing strategies
9. Persist to DB: Session, Recommendation, AgentLog
10. Cache result in Redis
11. Return PrismResponse

Library: uuid (stdlib), sqlalchemy (MIT), app.* (internal).
"""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session as DBSession

from app.agents.kismat import KismatTrustAgent
from app.agents.paisa import PaisaBudgetAgent
from app.agents.samay import SamayTimeAgent
from app.agents.soch import SochOrchestrator
from app.config import settings
from app.engines.confidence_genome import ConfidenceGenome
from app.engines.emotional_layer import EmotionalLayer
from app.engines.life_event_engine import LifeEventEngine
from app.engines.product_matcher import match_products
from app.engines.temporal_simulator import generate as temporal_generate
from app.models.orm_models import AgentLog, Recommendation, Session as SessionORM
from app.models.schemas import PrismRequest, PrismResponse
from app.utils.cache import cache_key, get_cached, set_cached
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Instantiate engines once — they are stateless and thread-safe
_event_engine = LifeEventEngine()
_emotional_layer = EmotionalLayer()
_kismat = KismatTrustAgent()
_paisa = PaisaBudgetAgent()
_samay = SamayTimeAgent()
_soch = SochOrchestrator()
_genome = ConfidenceGenome()


class PrismService:
    def __init__(self, db: DBSession):
        self.db = db

    async def analyze(self, request: PrismRequest) -> PrismResponse:
        session_id = str(uuid.uuid4())
        user_input = request.user_input
        user_pincode = request.user_pincode
        budget = request.budget

        logger.info(f"[{session_id}] Starting analysis: input='{user_input[:60]}'")

        # ── Step 1: Cache check ───────────────────────────────────────────
        ck = cache_key(user_input, user_pincode, str(budget))
        if settings.environment != "development":
            cached = get_cached(ck)
            if cached:
                logger.info(f"[{session_id}] Cache hit — returning cached result")
                return PrismResponse(**cached)

        # ── Step 2: Life event detection ──────────────────────────────────
        logger.info(f"[{session_id}] Detecting life event...")
        event_data = _event_engine.detect_event(user_input)
        inst_key, inst_data, state_key, state_data = _event_engine.detect_location(user_input)

        logger.info(
            f"[{session_id}] Event: {event_data['event_key']} "
            f"(confidence={event_data['confidence']:.2f}), "
            f"institution={inst_key}, state={state_key}"
        )

        # Enrich purchase phases with contextual notes
        enriched_phases = _event_engine.enrich_with_context(
            event_data["purchase_phases"], inst_data, state_data
        )

        # ── Step 3: Bharat context assembly ───────────────────────────────
        bharat_context = _build_bharat_context(inst_key, inst_data, state_key, state_data)

        # ── Step 4: Emotional opening message (LLM call 1) ─────────────────
        logger.info(f"[{session_id}] Generating emotional opening...")
        emotional_message = _emotional_layer.generate_opening(
            user_input=user_input,
            event_data=event_data,
            bharat_context={
                "institution_name": inst_data.get("display_name") if inst_data else None,
                "state_name": state_data.get("display_name") if state_data else None,
            },
        )

        # ── Step 5: Product matching ──────────────────────────────────────
        logger.info(f"[{session_id}] Matching products...")
        products = match_products(
            event_key=event_data["event_key"],
            institution_data=inst_data,
            budget=budget,
            pincode=user_pincode,
            limit=5,
        )

        if not products:
            raise ValueError(
                "No products found for this context. Try adjusting your budget or pincode."
            )

        top_product = products[0]
        logger.info(f"[{session_id}] Top product: {top_product['name']} @ Rs {top_product['price']}")

        # ── Step 6: Agent evaluation context ──────────────────────────────
        agent_context = {
            "budget": budget,
            "user_pincode": user_pincode,
            "urgency_days": event_data["timeline_days"],
            "detected_event": event_data["label"],
            "state": state_data.get("display_name") if state_data else "India",
            "event_key": event_data["event_key"],
        }

        # ── Step 7: Specialist agents (deterministic) ─────────────────────
        logger.info(f"[{session_id}] Running specialist agents...")
        kismat_result = _kismat.evaluate(top_product, agent_context)
        paisa_result = _paisa.evaluate(top_product, agent_context)
        samay_result = _samay.evaluate(top_product, agent_context)
        specialist_results = [kismat_result, paisa_result, samay_result]

        # ── Step 8: Soch deliberation (LLM call 2) ────────────────────────
        logger.info(f"[{session_id}] Soch deliberating...")
        soch_result = _soch.deliberate(specialist_results, top_product, agent_context)
        all_agent_results = specialist_results + [soch_result]

        # ── Step 9: Confidence genome ─────────────────────────────────────
        confidence_data = _genome.compute(
            specialist_results, soch_result, top_product, user_pincode
        )

        # ── Step 10: Temporal strategies ──────────────────────────────────
        logger.info(f"[{session_id}] Generating temporal strategies...")
        strategies = temporal_generate(top_product, agent_context)

        # ── Step 11: LLM roadmap (optional, only for high-confidence events) ─
        llm_roadmap = None
        if event_data.get("matched_keywords"):
            location_summary = _build_location_summary(inst_data, state_data)
            llm_roadmap = _event_engine.generate_llm_roadmap(
                event_data, location_summary, user_input
            )

        # ── Step 12: Persist to DB ────────────────────────────────────────
        logger.info(f"[{session_id}] Saving to database...")
        _persist_session(
            self.db, session_id, request, event_data, inst_key, state_key
        )
        _persist_recommendation(
            self.db, session_id, top_product, soch_result,
            confidence_data, strategies, emotional_message
        )
        _persist_agent_logs(self.db, session_id, all_agent_results, top_product)
        self.db.commit()

        # ── Step 13: Build response ───────────────────────────────────────
        response_data = PrismResponse(
            session_id=session_id,
            detected_event=event_data["label"],
            event_key=event_data["event_key"],
            emotion_level=event_data["emotion_level"],
            family_significance=event_data["family_significance"],
            emotional_message=emotional_message,
            purchase_timeline=enriched_phases,
            agent_debate=[
                {
                    "agent_name": r["agent_name"],
                    "agent_role": r["agent_role"],
                    "message": r["message"],
                    "score_contribution": r["score_contribution"],
                    "verdict": r["verdict"],
                    "data": r.get("data", {}),
                }
                for r in all_agent_results
            ],
            top_recommendation=top_product,
            confidence=confidence_data,
            temporal_strategies=strategies,
            bharat_context=bharat_context,
            state_detected=state_key,
            institution_detected=inst_key,
            llm_roadmap=llm_roadmap,
        )

        # ── Step 14: Cache the response ───────────────────────────────────
        set_cached(ck, response_data.model_dump())
        # response_data.confidence is now a ConfidenceBreakdown Pydantic object
        logger.info(f"[{session_id}] Analysis complete. Score: {response_data.confidence.total_score}")

        return response_data


# ─────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────

def _build_bharat_context(
    inst_key: Optional[str],
    inst_data: Optional[Dict],
    state_key: Optional[str],
    state_data: Optional[Dict],
) -> Dict:
    notes = []
    govt_note = None

    if inst_data:
        wattage = inst_data.get("appliance_wattage_limit")
        if wattage:
            notes.append(
                f"Appliances above {wattage}W are not permitted at "
                f"{inst_data.get('display_name', 'your institution')}."
            )
        prohibited = inst_data.get("prohibited_items", [])
        if prohibited:
            readable = [p.replace("_", " ") for p in prohibited]
            notes.append(f"Prohibited items: {', '.join(readable)}.")
        if inst_data.get("notes"):
            notes.append(inst_data["notes"])

    if state_data:
        climate = state_data.get("climate", "")
        if "humid" in climate:
            notes.append("High humidity in this region — prefer breathable fabrics and rust-resistant items.")
        if "arid" in climate or "desert" in climate:
            notes.append("Dry climate — dust-resistant products are a priority.")
        if state_data.get("notes", {}).get("water_filter_priority"):
            notes.append("Hard water in this region — a water filter is a worthwhile investment.")

    festivals = state_data.get("festivals", [])[:3] if state_data else None

    return {
        "institution_name": inst_data.get("display_name") if inst_data else None,
        "institution_type": inst_data.get("type") if inst_data else None,
        "state_name": state_data.get("display_name") if state_data else None,
        "wattage_limit": inst_data.get("appliance_wattage_limit") if inst_data else None,
        "relevant_festivals": festivals,
        "government_scheme_note": govt_note,
        "climate_note": state_data.get("climate", "").replace("_", " ").title() if state_data else None,
        "contextual_notes": notes if notes else None,
    }


def _build_location_summary(inst_data: Optional[Dict], state_data: Optional[Dict]) -> str:
    parts = []
    if inst_data:
        parts.append(f"{inst_data.get('display_name', 'an institution')} in {inst_data.get('city', '')}")
    if state_data:
        parts.append(state_data.get("display_name", ""))
    return ", ".join(filter(None, parts)) or "India"


def _persist_session(db, session_id, request, event_data, inst_key, state_key):
    session_row = SessionORM(
        id=session_id,
        user_input=request.user_input[:500],
        detected_event=event_data["label"],
        event_key=event_data["event_key"],
        emotion_level=event_data["emotion_level"],
        family_significance=event_data.get("family_significance"),
        state_detected=state_key,
        institution_detected=inst_key,
        user_pincode=request.user_pincode,
        budget=request.budget,
    )
    db.add(session_row)


def _persist_recommendation(db, session_id, product, soch_result, confidence_data, strategies, emotional_message):
    # confidence_data is a plain dict from ConfidenceGenome.compute(); serialize safely
    confidence_dict = confidence_data if isinstance(confidence_data, dict) else confidence_data.model_dump()
    rec_row = Recommendation(
        id=str(uuid.uuid4()),
        session_id=session_id,
        product_id=product.get("id", ""),
        product_name=product.get("name", ""),
        final_verdict=soch_result["verdict"],
        confidence_score=confidence_dict["total_score"],
        confidence_breakdown=confidence_dict,
        temporal_strategies=strategies,
        emotional_message=emotional_message,
        soch_reasoning=soch_result["message"],
    )
    db.add(rec_row)


def _persist_agent_logs(db, session_id, agent_results, product):
    for result in agent_results:
        log_row = AgentLog(
            session_id=session_id,
            agent_name=result["agent_name"],
            agent_role=result["agent_role"],
            verdict=result["verdict"],
            message=result["message"],
            score_contribution=result["score_contribution"],
            input_snapshot={
                "product_id": product.get("id"),
                "product_name": product.get("name"),
                "price": product.get("price"),
            },
        )
        db.add(log_row)
