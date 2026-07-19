"""
memory_service.py — Read, update, and apply user memory for personalisation.

HOW PERSONALISATION WORKS:
1. Before analysis: read user memory, build a personalisation context
2. During RAG retrieval: boost products matching user's preferred categories
3. During agent evaluation: adjust confidence based on user's price range
4. After analysis: update memory with new learnings from this session

WHAT GETS LEARNED:
- Every search category is added to searched_categories (frequency weighted)
- Every budget input refines preferred_price_range
- Every life event is logged to life_events_history
- Every chosen product's id goes to liked_product_ids
- If Soch REJECT happens 3+ times for same category → disliked_categories
- Location mentioned → location_hints (most recent 3 kept)
- Persona tags are inferred: student, new_parent, professional, budget_conscious, premium

PERSONA TAG INFERENCE RULES:
- session_count >= 5 and avg searches in "electronics" → "tech_enthusiast"
- life_events includes "hostel_move" → "student"
- life_events includes "new_baby" → "new_parent"
- preferred_price_range[1] < 5000 → "budget_conscious"
- preferred_price_range[0] > 20000 → "premium_buyer"
- life_events includes "first_job" → "young_professional"
"""

from datetime import datetime
from sqlalchemy.orm import Session
from app.models.orm_models import UserMemory
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_user_memory(db: Session, user_id: str) -> dict:
    """Return user memory as a plain dict for use in analysis."""
    memory = db.query(UserMemory).filter(UserMemory.user_id == user_id).first()
    if not memory:
        return _empty_memory()
    return {
        "searched_categories": memory.searched_categories or [],
        "preferred_price_range": memory.preferred_price_range or [0, 50000],
        "life_events_history": memory.life_events_history or [],
        "liked_product_ids": memory.liked_product_ids or [],
        "disliked_categories": memory.disliked_categories or [],
        "location_hints": memory.location_hints or [],
        "persona_tags": memory.persona_tags or [],
        "session_count": memory.session_count or 0,
        "last_intent": memory.last_intent,
        "last_event_key": memory.last_event_key,
        "last_location": memory.last_location,
        "stated_budget": memory.stated_budget,
    }


def build_personalisation_context(memory: dict, current_request: dict) -> dict:
    """
    Build a personalisation context that modifies RAG retrieval and agent scoring.
    Returns a dict that gets passed into retrieve_products() and agent evaluations.
    """
    persona_tags = memory.get("persona_tags", [])
    price_range = memory.get("preferred_price_range", [0, 50000])
    disliked = memory.get("disliked_categories", [])
    liked_ids = memory.get("liked_product_ids", [])
    history = memory.get("life_events_history", [])
    location_hints = memory.get("location_hints", [])
    session_count = memory.get("session_count", 0)

    # Build a natural language personalisation hint for the LLM
    persona_lines = []
    if "student" in persona_tags:
        persona_lines.append("This user is a student — prefer budget-friendly, hostel-compatible products.")
    if "budget_conscious" in persona_tags:
        persona_lines.append(f"This user prefers products under Rs {price_range[1]}.")
    if "premium_buyer" in persona_tags:
        persona_lines.append("This user prefers premium products — quality over price.")
    if "new_parent" in persona_tags:
        persona_lines.append("This user has a newborn — safety and quality are top priorities.")
    if "young_professional" in persona_tags:
        persona_lines.append("This user recently started a job — professional appearance matters.")
    if disliked:
        persona_lines.append(f"Avoid recommending from: {', '.join(disliked)}.")
    if location_hints:
        persona_lines.append(f"User has been in: {', '.join(location_hints[-2:])}.")
    if session_count > 0:
        persona_lines.append(f"Returning user — {session_count} previous sessions.")

    return {
        "persona_hint": " ".join(persona_lines),
        "preferred_max_price": price_range[1],
        "preferred_min_price": price_range[0],
        "disliked_categories": disliked,
        "liked_product_ids": liked_ids,
        "persona_tags": persona_tags,
        "is_returning_user": session_count > 0,
        "last_location": memory.get("last_location"),
        "session_count": session_count,
    }


def update_memory_after_analysis(
    db: Session,
    user_id: str,
    analysis_result: dict,
    request_data: dict,
) -> None:
    """
    Update user memory after each analysis session.
    Called at the end of prism_service.analyze().
    """
    memory = db.query(UserMemory).filter(UserMemory.user_id == user_id).first()
    if not memory:
        memory = UserMemory(user_id=user_id)
        db.add(memory)

    # Increment session count
    memory.session_count = (memory.session_count or 0) + 1

    # Update searched categories
    new_category = analysis_result.get("top_recommendation", {}).get("category")
    if new_category:
        cats = list(memory.searched_categories or [])
        cats.append(new_category)
        memory.searched_categories = cats[-20:]  # keep last 20

    # Update price range learning
    budget = request_data.get("budget")
    if budget:
        old_range = memory.preferred_price_range or [0, 50000]
        # Smooth update — don't jump to extremes
        new_max = int((old_range[1] * 0.7) + (budget * 0.3))
        memory.preferred_price_range = [0, new_max]
        memory.stated_budget = budget

    # Update life events history
    event_key = analysis_result.get("event_key") or analysis_result.get("detected_event", "")
    if event_key and event_key != "general":
        events = list(memory.life_events_history or [])
        if event_key not in events:
            events.append(event_key)
        memory.life_events_history = events[-10:]  # keep last 10

    # Update location hints
    location = analysis_result.get("state_detected") or request_data.get("extracted_location")
    if location and location != "general":
        locs = list(memory.location_hints or [])
        if location not in locs:
            locs.append(location)
        memory.location_hints = locs[-5:]  # keep last 5
        memory.last_location = location

    # Update last intent
    memory.last_intent = analysis_result.get("detected_event", "")
    memory.last_event_key = event_key

    # Infer persona tags
    memory.persona_tags = _infer_persona_tags(memory)

    memory.updated_at = datetime.utcnow()
    db.commit()
    logger.info(f"Memory updated for user {user_id}, session #{memory.session_count}")


def record_product_choice(db: Session, user_id: str, product_id: str) -> None:
    """Called when user clicks 'Choose this' on a product."""
    memory = db.query(UserMemory).filter(UserMemory.user_id == user_id).first()
    if not memory:
        return
    liked = list(memory.liked_product_ids or [])
    if product_id not in liked:
        liked.append(product_id)
    memory.liked_product_ids = liked[-30:]  # keep last 30 chosen products
    db.commit()


def _infer_persona_tags(memory: UserMemory) -> list:
    """Infer persona tags from accumulated memory."""
    tags = []
    events = memory.life_events_history or []
    price_range = memory.preferred_price_range or [0, 50000]
    cats = memory.searched_categories or []
    count = memory.session_count or 0

    if "hostel_move" in events or "government_exam" in events:
        tags.append("student")
    if "new_baby" in events:
        tags.append("new_parent")
    if "first_job" in events:
        tags.append("young_professional")
    if "wedding" in events:
        tags.append("recently_married")
    if "shop_opening" in events:
        tags.append("entrepreneur")
    if "travel_adventure" in events or "religious_travel" in events:
        tags.append("traveller")
    if price_range[1] < 5000:
        tags.append("budget_conscious")
    if price_range[0] > 20000:
        tags.append("premium_buyer")
    if cats.count("electronics") >= 3:
        tags.append("tech_enthusiast")
    if count >= 5:
        tags.append("power_user")

    return list(set(tags))


def _empty_memory() -> dict:
    return {
        "searched_categories": [],
        "preferred_price_range": [0, 50000],
        "life_events_history": [],
        "liked_product_ids": [],
        "disliked_categories": [],
        "location_hints": [],
        "persona_tags": [],
        "session_count": 0,
        "last_intent": None,
        "last_event_key": None,
        "last_location": None,
        "stated_budget": None,
    }
