"""
prism_service.py — Master orchestration service for PRISM.

WHY A SERVICE LAYER:
Route handlers should contain NO business logic — only HTTP concerns.
This service is the single place where all engines and agents are called
in sequence. It can be tested independently of HTTP, imported by tests,
or called by background workers.

ORCHESTRATION ORDER (Revised):
1. Check Redis cache (return immediately if cached result found)
2. LifeEventEngine.detect_event_with_llm(): SINGLE LLM call for event + location +
   cultural context + product needs + emotional message + purchase phases.
   Fallback: keyword detect_event() + string detect_location() if LLM fails.
3. ProductMatcher: filter and semantically score top candidates using LLM product_needs
4. Kismat, Paisa, Samay: evaluate top product (deterministic numeric agents)
5. SochOrchestrator: synthesise with full cultural context (LLM call 2)
6. ConfidenceGenome: decompose score into factors
7. TemporalSimulator: generate 3 timing strategies using LLM-detected budget context
8. Persist to DB: Session, Recommendation, AgentLog
9. Cache result in Redis
10. Return PrismResponse

Library: uuid (stdlib), sqlalchemy (MIT), app.* (internal).
"""

import asyncio
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

        logger.info(f"[{session_id}] Starting analysis: input='{user_input[:80]}'")

        # ── Step 1: Cache check ────────────────────────────────────────────
        ck = cache_key(user_input, user_pincode, str(budget), str(request.target_date or ""))
        cached = get_cached(ck)
        if cached:
            logger.info(f"[{session_id}] Cache hit — returning cached result")
            return PrismResponse(**cached)

        # ── Step 2: LLM-First Event + Context Detection ───────────────────
        # This single call replaces: detect_event() + detect_location() + generate_llm_roadmap()
        logger.info(f"[{session_id}] Running LLM-first event + context detection...")
        llm_detection = _event_engine.detect_event_with_llm(user_input)

        # ── Step 3: Build canonical event_data and context ────────────────
        inst_key = None
        inst_data = None
        state_key = None
        state_data = None
        cultural_context = None
        climate_product_note = None
        emotional_message = ""
        exact_items = []
        enriched_phases = []
        llm_roadmap_used = False

        if llm_detection:
            # ── LLM path (primary) ────────────────────────────────────────
            logger.info(f"[{session_id}] LLM detection succeeded: event={llm_detection.get('event_key')} location={llm_detection.get('detected_location', {}).get('place_name')}")

            event_data = {
                "event_key": llm_detection.get("event_key", "generic"),
                "label": llm_detection.get("event_label", "Shopping Assistance"),
                "timeline_days": llm_detection.get("timeline_days", 30),
                "purchase_phases": llm_detection.get("purchase_phases", []),
                "emotion_level": llm_detection.get("emotion_level", "moderate"),
                "family_significance": llm_detection.get("family_significance", "moderate"),
                "suggested_budget_range": {"min": 1000, "max": 50000},
                "confidence": 0.95,  # LLM detection is high-confidence
                "matched_keywords": [],
            }

            cultural_context = llm_detection.get("cultural_context")
            climate_product_note = llm_detection.get("climate_product_note")
            emotional_message = llm_detection.get("emotional_message", "")
            exact_items = llm_detection.get("exact_items_requested", [])
            enriched_phases = llm_detection.get("purchase_phases", [])
            llm_roadmap_used = True

            # Resolve location from LLM detection
            loc = llm_detection.get("detected_location", {})
            llm_state_key = loc.get("state_key")
            if llm_state_key:
                state_key = llm_state_key
                state_data = _event_engine.get_state_data_for_key(llm_state_key)
                if not state_data and llm_state_key:
                    # LLM may have used a key not in our DB — build minimal state_data from LLM context
                    state_data = {
                        "display_name": loc.get("place_name", llm_state_key.replace("_", " ").title()),
                        "climate": loc.get("climate", "moderate"),
                        "festivals": [],
                        "regional_preferences": {},
                        "notes": {},
                        "llm_generated": True,
                    }

            # Also try institution detection via keyword fallback
            inst_key_fallback, inst_data_fallback, _, _ = _event_engine.detect_location(user_input)
            if inst_key_fallback:
                inst_key = inst_key_fallback
                inst_data = inst_data_fallback
                # If institution has a state, prefer that
                if inst_data and not state_data:
                    inst_state = inst_data.get("state")
                    state_data = _event_engine.get_state_data_for_key(inst_state)
                    state_key = inst_state

            # Enrich phases with institution constraints + climate notes
            enriched_phases = _event_engine.enrich_with_context(
                enriched_phases, inst_data, state_data,
                cultural_context=cultural_context,
                climate_note=climate_product_note,
            )

        else:
            # ── Fallback keyword path ─────────────────────────────────────
            logger.warning(f"[{session_id}] LLM detection failed — falling back to keyword detection")
            event_data = _event_engine.detect_event(user_input)
            inst_key, inst_data, state_key, state_data = _event_engine.detect_location(user_input)

            logger.info(
                f"[{session_id}] [FALLBACK] Event: {event_data['event_key']} "
                f"(confidence={event_data['confidence']:.2f}), "
                f"institution={inst_key}, state={state_key}"
            )

            # Fallback LLM roadmap (uses the old approach)
            location_summary = _build_location_summary(inst_data, state_data)
            llm_result = _event_engine.generate_llm_roadmap(event_data, location_summary, user_input)
            if llm_result:
                emotional_message = llm_result.get("emotional_message", "")
                exact_items = llm_result.get("exact_items_requested", [])
                dynamic_phases = llm_result.get("purchase_phases", [])
                if dynamic_phases:
                    enriched_phases = _event_engine.enrich_with_context(
                        dynamic_phases, inst_data, state_data
                    )
                    llm_roadmap_used = True
                else:
                    enriched_phases = _event_engine.enrich_with_context(
                        event_data["purchase_phases"], inst_data, state_data
                    )
            else:
                enriched_phases = _event_engine.enrich_with_context(
                    event_data["purchase_phases"], inst_data, state_data
                )

            if not emotional_message:
                emotional_message = _emotional_layer.generate_opening(
                    user_input=user_input,
                    event_data=event_data,
                    bharat_context={
                        "institution_name": inst_data.get("display_name") if inst_data else None,
                        "state_name": state_data.get("display_name") if state_data else None,
                    },
                )

        # ── Step 3.5: Handle unsupported non-retail requests ─────────────
        is_supported = llm_detection.get("is_supported_retail_query", True) if llm_detection else True
        if not is_supported or event_data.get("event_key") == "unsupported" or (not enriched_phases and not exact_items):
            logger.info(f"[{session_id}] Gracefully rejecting unsupported request: {event_data.get('intent')}")
            
            # Use the LLM's apology if provided, else generic fallback
            apology = emotional_message or "I'm sorry, I specialize in retail shopping and event planning on Meesho. I cannot help with things like flights, cars, stocks, or general knowledge."
            
            response_data = PrismResponse(
                session_id=session_id,
                detected_event="Unsupported Request",
                event_key="unsupported",
                emotion_level="low",
                family_significance="moderate",
                emotional_message=apology,
                purchase_timeline=[],
                agent_debate=[],
                top_recommendation={},
                all_products=[],
                confidence={"total_score": 0.0, "base_score": 0, "factors": [], "interpretation": "Unsupported"},
                temporal_strategies=[],
                bharat_context={"state_name": None, "institution_name": None},
                state_detected=None,
                institution_detected=None,
                llm_roadmap=None,
                detected_intent=event_data.get("intent")
            )
            set_cached(ck, response_data.model_dump())
            return response_data

        # ── Step 4: Apply target_date override ───────────────────────────
        if request.target_date:
            try:
                from datetime import datetime
                target = datetime.strptime(request.target_date, "%Y-%m-%d")
                delta = (target - datetime.now()).days
                event_data["timeline_days"] = max(1, delta)
                logger.info(f"[{session_id}] Overrode timeline_days with user target_date: {event_data['timeline_days']} days")
            except Exception as e:
                logger.warning(f"Failed to parse target_date {request.target_date}: {e}")

        # ── Step 5: Build Bharat context for UI display ───────────────────
        bharat_context = _build_bharat_context(
            inst_key, inst_data, state_key, state_data, event_data,
            cultural_context=cultural_context,
            climate_product_note=climate_product_note,
            llm_detection=llm_detection,
        )

        # ── Step 6: Extract all categories from phases ────────────────────
        all_categories = []
        suggested_items_with_categories = {}
        for phase in enriched_phases:
            phase_cats = phase.get("categories", [])
            all_categories.extend(phase_cats)
            for item in phase.get("suggested_items", []):
                # Map the suggested item to the first category of this phase (or generic)
                suggested_items_with_categories[item] = phase_cats[0] if phase_cats else "generic"
        
        # Also include LLM's direct category_mapping
        if llm_detection and llm_detection.get("category_mapping"):
            all_categories.extend(llm_detection["category_mapping"])
        # Deduplicate
        all_categories = list(dict.fromkeys(all_categories))

        # ── Step 7: Product matching ──────────────────────────────────────
        logger.info(f"[{session_id}] Matching products... exact_items: {exact_items}, suggested: {list(suggested_items_with_categories.keys())}, categories: {all_categories}")

        # Build semantic search context for product matcher
        product_search_context = {
            "user_input": user_input,
            "cultural_context": cultural_context,
            "climate_note": climate_product_note,
            "product_needs": llm_detection.get("product_needs", []) if llm_detection else [],
        }

        products = match_products(
            event_key=event_data["event_key"],
            institution_data=inst_data,
            budget=budget,
            pincode=user_pincode,
            limit=50,
            categories=all_categories,
            exact_items=exact_items,
            suggested_items_with_categories=suggested_items_with_categories,
            product_search_context=product_search_context,
        )

        if not products:
            logger.info(f"[{session_id}] No products found for this context.")
            empty_product = {
                "id": "NONE",
                "name": "No relevant products found in your area",
                "category": "system",
                "price": 0,
                "seller_name": "PRISM Notify",
                "seller_rating": 0,
                "stock_status": "out_of_stock",
                "image_placeholder": "out_of_stock",
                "description": "We currently do not have items that match your specific context and pincode."
            }
            empty_confidence = {
                "total_score": 0.0,
                "base_score": 0,
                "factors": [],
                "interpretation": "No products available."
            }
            empty_strategies = [
                {
                    "strategy_name": "Notify Me",
                    "strategy_key": "wait",
                    "price": 0,
                    "savings_vs_now": 0,
                    "recommended": True,
                    "note": "We have saved your preference and will notify you as soon as relevant products appear in our catalog.",
                    "action_date": "We will keep you posted",
                }
            ]
            empty_timeline = [
                {
                    "phase_name": "Waiting for Inventory",
                    "days_from_now": 0,
                    "categories": [],
                    "priority": "must_have",
                    "note": "We are currently scanning our suppliers. We will notify you when matching products arrive."
                }
            ]
            empty_emotional_message = (
                f"We searched our catalog for {event_data.get('label', 'your')} items, "
                f"but currently don't have matching products that pass our quality checks for your area. "
                f"We have saved your requirement and will notify you the moment relevant items become available!"
            )
            response_data = PrismResponse(
                session_id=session_id,
                detected_event=event_data["label"],
                event_key=event_data["event_key"],
                emotion_level=event_data["emotion_level"],
                family_significance=event_data["family_significance"],
                emotional_message=empty_emotional_message,
                purchase_timeline=empty_timeline,
                agent_debate=[],
                top_recommendation=empty_product,
                all_products=[],
                confidence=empty_confidence,
                temporal_strategies=empty_strategies,
                bharat_context=bharat_context,
                state_detected=state_key,
                institution_detected=inst_key,
                llm_roadmap=None,
                detected_intent=llm_detection.get("intent") if llm_detection else None,
            )
            set_cached(ck, response_data.model_dump())
            return response_data

        # ── Pick top_product: always an in-stock item ─────────────────────
        # OOS dummy cards may be prepended at index 0; skip them so their
        # zero ratings never poison the agent debate or confidence genome.
        in_stock_products = [p for p in products if p.get("stock_status") != "out_of_stock"]
        top_product = in_stock_products[0] if in_stock_products else products[0]
        logger.info(f"[{session_id}] Top product for debate: {top_product['name']} @ Rs {top_product['price']}")

        # ── Step 8: Agent evaluation context ──────────────────────────────
        # Pass full cultural context to all agents so their messages are relevant
        agent_context = {
            "budget": budget,
            "user_input": user_input,
            "user_pincode": user_pincode,
            "urgency_days": event_data["timeline_days"],
            "detected_event": event_data["label"],
            "state": state_data.get("display_name") if state_data else "India",
            "event_key": event_data["event_key"],
            "cultural_context": cultural_context or "General India",
            "location_context": (
                llm_detection.get("detected_location", {}).get("place_name", "India")
                if llm_detection else "India"
            ),
            "climate_context": (
                llm_detection.get("detected_location", {}).get("climate", "")
                if llm_detection else ""
            ),
            "budget_constraint_detected": (
                llm_detection.get("budget_constraint_detected", False)
                if llm_detection else False
            ),
            "intent": llm_detection.get("intent", "") if llm_detection else "",
        }

        # ── Step 9: Specialist agents — all three run in parallel via thread pool ───
        logger.info(f"[{session_id}] Running specialist agents in parallel...")
        kismat_result, paisa_result, samay_result = await asyncio.gather(
            asyncio.to_thread(_kismat.evaluate, top_product, agent_context),
            asyncio.to_thread(_paisa.evaluate, top_product, agent_context),
            asyncio.to_thread(_samay.evaluate, top_product, agent_context),
        )
        specialist_results = [kismat_result, paisa_result, samay_result]

        # ── Step 10: Soch deliberation — full cultural context ─────────────
        logger.info(f"[{session_id}] Soch deliberating with cultural context...")
        soch_result = _soch.deliberate(specialist_results, top_product, agent_context)
        all_agent_results = specialist_results + [soch_result]

        # ── Step 11: Confidence genome ─────────────────────────────────────
        confidence_data = _genome.compute(
            specialist_results, soch_result, top_product, user_pincode
        )

        # ── Step 12: Temporal strategies ──────────────────────────────────
        logger.info(f"[{session_id}] Generating temporal strategies...")
        strategies = temporal_generate(top_product, agent_context)

        # ── Step 13: Persist to DB ────────────────────────────────────────
        logger.info(f"[{session_id}] Saving to database...")
        _persist_session(self.db, session_id, request, event_data, inst_key, state_key)
        _persist_recommendation(
            self.db, session_id, top_product, soch_result,
            confidence_data, strategies, emotional_message
        )
        _persist_agent_logs(self.db, session_id, all_agent_results, top_product)
        self.db.commit()

        # ── Step 14: Enrich all products and Build response ───────────────
        for prod in products:
            prod["temporal_strategies"] = temporal_generate(prod, agent_context)
            
            p_k = _kismat.evaluate(prod, agent_context)
            p_p = _paisa.evaluate(prod, agent_context)
            p_s = _samay.evaluate(prod, agent_context)
            p_genome = _genome.compute([p_k, p_p, p_s], None, prod, user_pincode)
            prod["confidence_score"] = p_genome["total_score"]

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
            all_products=products,
            confidence=confidence_data,
            temporal_strategies=strategies,
            bharat_context=bharat_context,
            state_detected=state_key,
            institution_detected=inst_key,
            llm_roadmap="LLM-first unified detection" if llm_roadmap_used else None,
            detected_intent=llm_detection.get("intent") if llm_detection else None,
        )

        # ── Step 15: Cache the response ───────────────────────────────────
        set_cached(ck, response_data.model_dump())
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
    event_data: Dict,
    cultural_context: Optional[str] = None,
    climate_product_note: Optional[str] = None,
    llm_detection: Optional[Dict] = None,
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

    if state_data and not state_data.get("llm_generated"):
        climate = state_data.get("climate", "")
        if "humid" in climate:
            notes.append("High humidity in this region — prefer breathable fabrics and rust-resistant items.")
        if "arid" in climate or "desert" in climate:
            notes.append("Dry climate — dust-resistant products are a priority.")
        if state_data.get("notes", {}).get("water_filter_priority"):
            notes.append("Hard water in this region — a water filter is a worthwhile investment.")
        if "mountain" in climate or "alpine" in climate or "cold" in climate:
            notes.append("Cold mountain climate — thermal and woolen products are essential.")

    # Add LLM-generated cultural context as a note
    if cultural_context:
        notes.append(f"Cultural context: {cultural_context}")
    if climate_product_note:
        notes.append(f"Climate tip: {climate_product_note}")

    festivals = state_data.get("festivals", [])[:3] if state_data else []

    if event_data.get("event_key") == "festival_prep":
        for kw in event_data.get("matched_keywords", []):
            if kw.title() not in festivals:
                festivals.append(kw.title())
        if not festivals:
            festivals.append("Upcoming Local Festival")

    # Determine display names
    location_display = None
    if llm_detection and llm_detection.get("detected_location", {}).get("place_name"):
        location_display = llm_detection["detected_location"]["place_name"]
    elif state_data:
        location_display = state_data.get("display_name")

    climate_note_display = None
    if llm_detection and llm_detection.get("detected_location", {}).get("climate"):
        climate_note_display = llm_detection["detected_location"]["climate"].replace("_", " ").title()
    elif state_data:
        climate_note_display = state_data.get("climate", "").replace("_", " ").title()

    return {
        "institution_name": inst_data.get("display_name") if inst_data else None,
        "institution_type": inst_data.get("type") if inst_data else None,
        "state_name": location_display,
        "wattage_limit": inst_data.get("appliance_wattage_limit") if inst_data else None,
        "relevant_festivals": festivals,
        "government_scheme_note": govt_note,
        "climate_note": climate_note_display,
        "contextual_notes": notes if notes else None,
        "cultural_context": cultural_context,
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
