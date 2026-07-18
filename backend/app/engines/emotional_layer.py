"""
emotional_layer.py — Detects emotional register and generates warm opening messages.

WHY THIS MODULE EXISTS:
Indian commerce decisions are deeply emotional — a hostel move represents a family's
aspirations, a wedding involves years of savings. Generic product text ignores this
entirely. The emotional layer ensures PRISM's first words to the user acknowledge
the human moment before discussing products.

REGISTER CLASSIFICATION:
Three registers map to the emotional weight of the event:
- warm_friend: For very high emotion + very high family significance
- caring_advisor: For high emotion events
- helpful_assistant: For lower-stakes, transactional contexts

WHY LLM HERE:
Register switching and tone calibration require nuanced language understanding
that deterministic templates cannot produce. One LLM call produces a message
that feels genuinely written for this user's specific situation.

Library: groq (Apache 2.0), app.config (internal).
"""

from app.config import settings
from app.utils.groq_client import groq_chat
from typing import Dict, Any

# Emotion level to numeric weight for register classification
_EMOTION_WEIGHT = {
    "very_high": 3,
    "high": 2,
    "moderate": 1,
    "low": 0,
}

_SIGNIFICANCE_WEIGHT = {
    "extremely_high": 3,
    "very_high": 2,
    "high": 1,
    "moderate": 0,
}

_REGISTER_PROMPTS = {
    "warm_friend": (
        "Write as a very close friend who genuinely shares this joy. "
        "Your tone is warm, celebratory, and personal. "
        "You understand what this moment means to the family."
    ),
    "caring_advisor": (
        "Write as a trusted elder or older sibling. "
        "Your tone is warm, supportive, and gently encouraging. "
        "Acknowledge the excitement and the responsibility together."
    ),
    "helpful_assistant": (
        "Write as a knowledgeable, friendly shopping assistant. "
        "Your tone is helpful, clear, and professional but not cold. "
        "Focus on being useful."
    ),
}


class EmotionalLayer:
    """Classifies emotional register and generates personalised opening messages."""

    def classify_register(self, emotion_level: str, family_significance: str) -> str:
        """
        Returns one of three register strings based on emotion and family significance.
        Higher combined weight = warmer, more personal register.
        """
        emotion_w = _EMOTION_WEIGHT.get(emotion_level, 1)
        significance_w = _SIGNIFICANCE_WEIGHT.get(family_significance, 1)
        combined = emotion_w + significance_w

        if combined >= 4:
            return "warm_friend"
        elif combined >= 2:
            return "caring_advisor"
        else:
            return "helpful_assistant"

    def generate_opening(
        self,
        user_input: str,
        event_data: Dict[str, Any],
        bharat_context: Dict[str, Any],
    ) -> str:
        """
        Calls Claude with a structured prompt to produce a personalised opening
        message. The message acknowledges the life moment before any product talk.

        Args:
            user_input: The original user query.
            event_data: Output from LifeEventEngine.detect_event()
            bharat_context: Dict containing institution_name, state_name, climate_note.

        Returns:
            A 2-4 sentence warm opening message string.
        """
        register = self.classify_register(
            event_data.get("emotion_level", "high"),
            event_data.get("family_significance", "high"),
        )
        register_instruction = _REGISTER_PROMPTS.get(register, _REGISTER_PROMPTS["helpful_assistant"])

        institution_line = ""
        if bharat_context.get("institution_name"):
            institution_line = (
                f"The user is connected to {bharat_context['institution_name']}. "
                f"Acknowledge this if it feels natural."
            )

        state_line = ""
        if bharat_context.get("state_name"):
            state_line = f"The user is from or in {bharat_context['state_name']}."

        prompt = f"""You are writing the opening message for PRISM, an AI shopping assistant that cares deeply about Indian families.

{register_instruction}

Life event: {event_data['label']}
What the user said: "{user_input}"
{institution_line}
{state_line}

Write 2 to 3 sentences ONLY. Rules:
1. DO NOT list any products, categories, or prices.
2. DO NOT use corporate language like "I'm here to assist you" or "Let me help you".
3. DO NOT start with "I". Start with the emotion or the moment.
4. Acknowledge the life event specifically — not generically.
5. End with a natural transition to the shopping plan (one brief sentence).
6. Write in warm, simple Indian English. Use ONLY English, absolutely no Hindi or other language mixed in.
7. Maximum 60 words total."""

        try:
            response = groq_chat(
                model=settings.llm_model,
                max_tokens=settings.llm_max_tokens_emotional,
                temperature=settings.llm_temperature,
                messages=[{"role": "user", "content": prompt}],
                timeout=15.0,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Emotional Layer LLM Error: {e}")
            return "Congratulations on this new moment! Let's get you set up with everything you need."
