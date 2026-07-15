"""
life_event_engine.py — LLM-powered event detection and purchase timeline generator.

WHAT CHANGED FROM v1:
The previous version used keyword scanning across life_event_templates.json to detect
events. This failed for natural language ("going trekking to Kashmir", "daughter just
got married") because users never write the exact keywords we anticipated.

This version makes a single LLM call with a structured extraction prompt. Claude reads
the user's full natural language input and returns a JSON object with event_key,
location, season, cultural context, urgency, and emotion — all in one pass.

This is more accurate, handles synonyms naturally, understands regional phrasing,
and requires zero keyword maintenance.

Libraries: anthropic (Anthropic Terms), json (stdlib), app.config (internal).
"""

import json
import os
from typing import Optional
from anthropic import Anthropic
from app.config import settings

client = Anthropic(api_key=settings.anthropic_api_key)

# Load static data once at module level — not on every request
_TEMPLATES_PATH = os.path.join(os.path.dirname(__file__), "../data/life_event_templates.json")
_BHARAT_PATH = os.path.join(os.path.dirname(__file__), "../data/bharat_context.json")

with open(_TEMPLATES_PATH, encoding="utf-8") as f:
    _TEMPLATES = json.load(f)

with open(_BHARAT_PATH, encoding="utf-8") as f:
    _BHARAT = json.load(f)

# Build valid event keys from templates file — no hardcoding
VALID_EVENT_KEYS = list(_TEMPLATES.keys()) + ["travel_adventure", "religious_pilgrimage", "general"]

PARSE_PROMPT = """You are a context extraction engine for PRISM, an AI commerce assistant built for India.

A user has described their situation in natural language. Extract structured information and return ONLY a valid JSON object — no explanation, no markdown, no preamble.

Valid event_key values: {valid_keys}

Extract:
{{
  "event_key": "the best matching event key from the valid list above",
  "confidence": float between 0.0 and 1.0,
  "detected_location": "city or region name, or null",
  "detected_state": "Indian state name in snake_case (e.g. tamil_nadu, jammu_and_kashmir), or null",
  "season": "summer | monsoon | winter | spring | null",
  "cultural_context": ["list of relevant cultural notes, e.g. kashmir_muslim_majority, high_altitude, coastal_region, joint_family, first_generation_college"],
  "travel_purpose": "trek | pilgrimage | tourism | work | null",
  "urgency_days": "integer estimate of days until the event, or null if unclear",
  "budget_mentioned": "integer in rupees, or null if not mentioned",
  "emotion_level": "very_high | high | medium | low",
  "family_significance": "first_in_family | milestone | routine | null",
  "institution_mentioned": "exact name of college, hospital, or government body, or null"
}}

Examples of correct extraction:
- "going trekking to Kashmir next month, want to dress right for local culture" →
  event_key: travel_adventure, detected_state: jammu_and_kashmir, season: depends on month, cultural_context: [kashmir_muslim_majority, high_altitude], travel_purpose: trek

- "daughter got into NIT Trichy starting August" →
  event_key: hostel_move, detected_state: tamil_nadu, institution_mentioned: NIT Trichy, urgency_days: estimate from today to August

- "Diwali shopping for the family, budget around 5000" →
  event_key: festival_prep, season: autumn, budget_mentioned: 5000, emotion_level: high

- "son got into IIT Bombay, first in our family to go to IIT" →
  event_key: hostel_move, institution_mentioned: IIT Bombay, detected_state: maharashtra, family_significance: first_in_family, emotion_level: very_high

User input: "{user_input}"

Return ONLY the JSON object."""


ROADMAP_PROMPT = """You are PRISM, an AI commerce brain built for India's next 500 million internet users.

A user is going through this life event: {event_key_label}
Their location: {location}
Season: {season}
Cultural context: {cultural_notes}
Detected institution: {institution}

Write a warm, specific 2-sentence purchase roadmap introduction in simple Indian English.
- Sentence 1: Acknowledge what is happening and what makes this situation unique (mention specific location/institution if detected)
- Sentence 2: Set up what the purchase plan will cover

Do NOT list products. Do NOT use corporate language. Write like a thoughtful older friend who knows India well.
Keep it under 60 words total."""


class LifeEventEngine:

    def detect_event(self, user_input: str) -> dict:
        """
        Uses Claude to extract structured event data from raw user input.
        Returns a dict with event_key, location, cultural context, urgency, etc.
        Falls back to a safe default if the LLM call fails or returns unparseable JSON.
        """
        try:
            response = client.messages.create(
                model=settings.llm_model,
                max_tokens=400,
                temperature=0,  # deterministic — we want consistent JSON parsing
                messages=[{
                    "role": "user",
                    "content": PARSE_PROMPT.format(
                        valid_keys=", ".join(VALID_EVENT_KEYS),
                        user_input=user_input
                    )
                }]
            )
            raw = response.content[0].text.strip()
            # Strip markdown fences if model adds them despite instructions
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            parsed = json.loads(raw.strip())
            # Validate event_key falls in known set
            if parsed.get("event_key") not in VALID_EVENT_KEYS:
                parsed["event_key"] = "general"
            return parsed
        except Exception as e:
            # Safe fallback — system still works, just less personalised
            return {
                "event_key": "general",
                "confidence": 0.2,
                "detected_location": None,
                "detected_state": None,
                "season": None,
                "cultural_context": [],
                "travel_purpose": None,
                "urgency_days": None,
                "budget_mentioned": None,
                "emotion_level": "medium",
                "family_significance": None,
                "institution_mentioned": None,
                "_parse_error": str(e)
            }

    def get_template(self, event_key: str) -> dict:
        """Returns the purchase timeline template for a detected event."""
        return _TEMPLATES.get(event_key, _TEMPLATES.get("general", {}))

    def get_bharat_context(self, state: Optional[str]) -> dict:
        """Returns regional context for a detected state."""
        if not state:
            return {}
        states = _BHARAT.get("states", {})
        return states.get(state, {})

    def get_institution_data(self, institution_name: Optional[str]) -> dict:
        """Returns institution-specific constraints (wattage limits, prohibited items)."""
        if not institution_name:
            return {}
        institutions = _BHARAT.get("institutions", {})
        # Case-insensitive match
        name_lower = institution_name.lower().replace(" ", "_")
        for key, data in institutions.items():
            if key.lower() in name_lower or name_lower in key.lower():
                return data
        return {}

    def enrich_timeline(self, template: dict, bharat_ctx: dict, institution_data: dict) -> list:
        """
        Takes the raw purchase phase template and enriches each phase with
        context-specific notes (wattage limits, climate warnings, cultural notes).
        Returns a list of enriched phase dicts.
        """
        phases = template.get("purchase_phases", [])
        enriched = []
        wattage_limit = institution_data.get("appliance_wattage_limit")
        climate = bharat_ctx.get("climate", "")
        hard_water = bharat_ctx.get("hard_water", False)

        for phase in phases:
            enriched_phase = dict(phase)
            notes = []
            if wattage_limit and enriched_phase.get("week_number", 0) == 1:
                notes.append(f"Appliance limit: {wattage_limit}W — heavier items filtered out")
            if hard_water and any("iron" in item.lower() or "kettle" in item.lower()
                                   for item in enriched_phase.get("items", [])):
                notes.append(f"Hard water area — consider scale-resistant kettle")
            if climate and "cold" in climate.lower() and enriched_phase.get("priority") == "comfort":
                notes.append(f"Climate: {climate} — prioritise warm layers")
            enriched_phase["context_notes"] = notes
            enriched.append(enriched_phase)
        return enriched

    def generate_roadmap_intro(self, parsed_event: dict) -> str:
        """
        Calls Claude to write a 2-sentence personalised purchase plan introduction.
        Only called when confidence > 0.5 — for low-confidence events, returns a generic opener.
        """
        if parsed_event.get("confidence", 0) < 0.5:
            return "Here is a purchase plan based on your situation."

        template = self.get_template(parsed_event["event_key"])
        cultural_notes = ", ".join(parsed_event.get("cultural_context", [])) or "none detected"

        try:
            response = client.messages.create(
                model=settings.llm_model,
                max_tokens=settings.llm_max_tokens_event,
                temperature=0.4,
                messages=[{
                    "role": "user",
                    "content": ROADMAP_PROMPT.format(
                        event_key_label=template.get("label", parsed_event["event_key"]),
                        location=parsed_event.get("detected_location") or parsed_event.get("detected_state") or "India",
                        season=parsed_event.get("season") or "current season",
                        cultural_notes=cultural_notes,
                        institution=parsed_event.get("institution_mentioned") or "not specified"
                    )
                }]
            )
            return response.content[0].text.strip()
        except Exception:
            return f"Here is your personalised purchase plan for {template.get('label', 'this event')}."
