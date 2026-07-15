"""
life_event_engine.py — Detects life events and Bharat context from user input.

WHY THIS MODULE EXISTS:
The central intelligence of PRISM. By detecting the life event before product
matching, we ensure every product recommendation is contextually relevant. A
bedsheet recommendation for a hostel move is very different from a bedsheet
recommendation for a wedding — this engine makes that distinction.

DETECTION STRATEGY:
- All 8 event templates and ALL their keywords are loaded once at module load.
- detect_event() scores each template by keyword hit count, returns the winner.
- detect_location() scans institution keywords and state names dynamically from JSON.
- generate_llm_roadmap() calls Claude ONLY for high-confidence events to produce
  a personalised 2-sentence purchase plan intro.

Library: json (stdlib), re (stdlib), groq (Apache 2.0), app.config (internal).
Chosen: groq over LangChain for the LLM roadmap call because this is a single,
simple prompt with no chain — LangChain overhead is not justified here.
"""

import json
import os
import re
from typing import Dict, Any, Optional, Tuple

from groq import Groq
from app.config import settings

_client = Groq(api_key=settings.groq_api_key)

_TEMPLATES_PATH = os.path.join(os.path.dirname(__file__), "../data/life_event_templates.json")
_CONTEXT_PATH = os.path.join(os.path.dirname(__file__), "../data/bharat_context.json")

# Module-level cache — loaded once, reused for every request
_templates: Optional[Dict] = None
_context: Optional[Dict] = None


def _load_templates() -> Dict:
    global _templates
    if _templates is None:
        with open(_TEMPLATES_PATH, encoding="utf-8") as f:
            _templates = json.load(f)
    return _templates


def _load_context() -> Dict:
    global _context
    if _context is None:
        with open(_CONTEXT_PATH, encoding="utf-8") as f:
            _context = json.load(f)
    return _context


class LifeEventEngine:
    """Detects life events and geographic/institutional context from free text."""

    def detect_event(self, user_input: str) -> Dict[str, Any]:
        """
        Scans all 8 templates and their keywords. Returns the template with the
        most keyword matches. Falls back to 'festival_prep' if nothing matches.

        Returns a dict with: event_key, label, timeline_days, purchase_phases,
        emotion_level, family_significance, suggested_budget_range, confidence, matched_keywords
        """
        templates = _load_templates()
        text = user_input.lower()

        best_key = None
        best_score = 0
        best_template = None
        best_matched = []

        for event_key, template in templates.items():
            keywords = template.get("keywords", [])
            matched = [kw for kw in keywords if kw.lower() in text]
            score = len(matched)
            if score > best_score:
                best_score = score
                best_key = event_key
                best_template = template
                best_matched = matched

        # Fallback if no keyword matched
        if not best_key or best_score == 0:
            best_key = "festival_prep"
            best_template = templates["festival_prep"]
            best_matched = []

        confidence = min(1.0, best_score / max(3, 1))

        return {
            "event_key": best_key,
            "label": best_template["label"],
            "timeline_days": best_template["timeline_days"],
            "purchase_phases": best_template["purchase_phases"],
            "emotion_level": best_template["emotion_level"],
            "family_significance": best_template["family_significance"],
            "suggested_budget_range": best_template["suggested_budget_range"],
            "confidence": confidence,
            "matched_keywords": best_matched,
        }

    def detect_location(self, user_input: str) -> Tuple[Optional[str], Optional[Dict], Optional[str], Optional[Dict]]:
        """
        Scans for institution names and state names from bharat_context.json.
        All strings are loaded from JSON — nothing is hardcoded in this function.

        Returns: (institution_key, institution_data, state_key, state_data)
        """
        context = _load_context()
        text = user_input.lower()

        institution_key = None
        institution_data = None

        for key, inst in context.get("institutions", {}).items():
            for keyword in inst.get("keywords", []):
                if keyword.lower() in text:
                    institution_key = key
                    institution_data = inst
                    break
            if institution_key:
                break

        state_key = None
        state_data = None

        # Check if institution tells us the state
        if institution_data:
            inst_state = institution_data.get("state")
            if inst_state and inst_state in context.get("states", {}):
                state_key = inst_state
                state_data = context["states"][inst_state]

        # Also scan state display names and keys directly
        if not state_key:
            for key, state in context.get("states", {}).items():
                display = state.get("display_name", "").lower()
                dominant_lang = state.get("dominant_language", "").lower()
                if display in text or key.replace("_", " ") in text:
                    state_key = key
                    state_data = state
                    break

        return institution_key, institution_data, state_key, state_data

    def enrich_with_context(
        self,
        purchase_phases: list,
        institution_data: Optional[Dict],
        state_data: Optional[Dict],
    ) -> list:
        """
        Applies institution constraints and climate notes to purchase phase notes.
        Returns enriched phases with contextual additions.
        """
        enriched = []
        for phase in purchase_phases:
            note = phase.get("note", "")
            additions = []

            if institution_data:
                wattage = institution_data.get("appliance_wattage_limit")
                if wattage and "kitchen" in " ".join(phase.get("categories", [])).lower():
                    additions.append(
                        f"Note: {institution_data.get('display_name', 'Your institution')} "
                        f"limits appliances to {wattage}W — check before buying electrical items."
                    )

            if state_data:
                climate = state_data.get("climate", "")
                if "humid" in climate and "bedding" in " ".join(phase.get("categories", [])).lower():
                    additions.append("Choose breathable fabrics — the local climate is humid.")
                if "desert" in climate or "arid" in climate:
                    additions.append("Dust-resistant and cooling items are priority in this climate.")

            enriched_note = note + (" " + " ".join(additions) if additions else "")
            enriched.append({**phase, "note": enriched_note.strip()})

        return enriched

    def generate_llm_roadmap(
        self,
        event_data: Dict,
        location_summary: str,
        user_input: str,
    ) -> Optional[Dict]:
        """
        Calls Claude to produce a warm, personalised 2-sentence intro to the
        purchase plan AND dynamically tailors the purchase phases. 
        Only called for high-confidence event detections (score > 0).
        """
        prompt = f"""You are a caring Indian shopping assistant helping someone with a major life event.

Life event detected: {event_data['label']}
Location context: {location_summary}
What they said: "{user_input}"
Days until the event: {event_data['timeline_days']}

Task:
1. Write a 2-sentence warm emotional message acknowledging their specific situation. Do not list products or prices. Use warm Indian English.
2. Provide a 3-phase purchase timeline. STRICT RULE: If their event is less than 14 days away, NEVER use the word "Week" in phase_name. Use "Days 1-2", "Days 3-5", etc.
3. Extract any specific items they asked for into exact_items_requested.
4. CRITICAL: Any categories related to the items they specifically asked for MUST be included in the 'categories' array of the FIRST phase (Phase 1), so they get those items immediately.

Respond ONLY with valid JSON in this exact format:
{{
  "emotional_message": "Your 2 sentence message here.",
  "exact_items_requested": ["item1", "item2"],
  "purchase_phases": [
    {{
      "phase_name": "Phase 1: Immediate Needs (Days 1-2)",
      "days_from_now": 0,
      "categories": ["category_name"],
      "priority": "must_have",
      "note": "Why they need this now."
    }},
    {{
      "phase_name": "Phase 2: Mid-Preparation (Days 3-5)",
      "days_from_now": 3,
      "categories": ["category_name"],
      "priority": "nice_to_have",
      "note": "..."
    }},
    {{
      "phase_name": "Phase 3: Final Touches (Days 6-7)",
      "days_from_now": 6,
      "categories": ["category_name"],
      "priority": "nice_to_have",
      "note": "..."
    }}
  ]
}}
Make sure to provide exactly 3 phases. Valid categories to choose from: [bedding, study_accessories, personal_care, bags_luggage, kitchen_essentials, formal_wear, festival_decor, baby_products]. If their need is completely outside these, map it to the closest one (e.g. tools -> study_accessories/kitchen_essentials).
"""

        try:
            response = _client.chat.completions.create(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content.strip()
            return json.loads(content)
        except Exception as e:
            print(f"LLM Roadmap Generation Error: {e}")
            if 'content' in locals():
                print(f"Raw LLM Content was: {content}")
            return None
