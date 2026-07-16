"""
soch.py — Soch Orchestrator Agent for PRISM.

WHY THIS AGENT CALLS THE LLM (Groq, Apache 2.0):
The three specialist agents (Kismat, Paisa, Samay) use deterministic rule-based
logic — no LLM needed there because their verdicts are based on numeric thresholds.
Soch's job is different: it must synthesise potentially conflicting verdicts,
identify the real tradeoff in plain language, and make a final recommendation.
This is a reasoning task that benefits from LLM capability.

UPGRADE (v2): Soch now receives the user's original words, detected cultural context,
and location/climate context. This means Soch can say:
  "Given the cold mountain climate in Kashmir, waterproof durability outweighs
   the slight price concern — this trek bag is the right choice."
instead of a generic verdict that ignores why the person is buying.

Library: groq (Apache 2.0) — chosen for fast inference with OpenAI-compatible API.
"""

from groq import Groq
from app.config import settings
from app.agents.base_agent import BaseAgent
from typing import Dict, Any, List

_client = Groq(api_key=settings.groq_api_key)


class SochOrchestrator(BaseAgent):
    name = "Soch"
    role = "Orchestrator"
    personality = (
        "Listens to all agents, reads the full human context behind the purchase, "
        "identifies the real tradeoff, and makes the final call with full reasoning."
    )

    def evaluate(self, product: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Soch uses deliberate(), not evaluate()")

    def deliberate(
        self,
        agent_results: List[Dict],
        product: Dict,
        context: Dict,
    ) -> Dict:
        """
        Synthesises the three specialist agent verdicts, calls the LLM once
        to produce a 2-sentence final verdict that incorporates:
        - The user's original words (what they actually said)
        - Cultural and climate context
        - The numeric agent verdicts
        
        This produces contextually rich verdicts like:
        "For a Kashmir winter trek, warmth and durability matter more than price —
         this product's quality justifies the cost."
        """
        verdicts = [r["verdict"] for r in agent_results]
        total_contribution = sum(r["score_contribution"] for r in agent_results)
        raw_score = (
            settings.confidence_base_score
            + total_contribution
            + settings.confidence_pincode_match_boost
        )
        final_score = max(
            settings.confidence_min,
            min(settings.confidence_max, raw_score),
        )

        debate_lines = "\n".join([
            (
                f"{r['agent_name']} ({r['agent_role']}): {r['message']} "
                f"[Verdict: {r['verdict']}, Score: {r['score_contribution']:+.0f}]"
            )
            for r in agent_results
        ])

        # Rich context for culturally-aware synthesis
        cultural_context = context.get("cultural_context", "General India")
        location_context = context.get("location_context", "India")
        climate_context = context.get("climate_context", "")
        user_intent = context.get("intent", "")
        user_input_raw = context.get("user_input", "")

        # Build context lines only when they add real value
        context_lines = []
        if location_context and location_context != "India":
            context_lines.append(f"Location: {location_context}")
        if climate_context:
            context_lines.append(f"Climate: {climate_context}")
        if cultural_context and cultural_context != "General India":
            context_lines.append(f"Cultural context: {cultural_context}")
        if user_intent:
            context_lines.append(f"Core intent: {user_intent}")

        context_block = "\n".join(context_lines) if context_lines else "General Indian household purchase"

        prompt = f"""You are Soch, the orchestrator of PRISM — an AI commerce recommendation system built for India.

Three specialist agents have evaluated a product for a user. Read their analysis carefully, understand the full human context, identify the single most important tradeoff, and deliver your final verdict in exactly 2 sentences.

Product: {product.get('name')} at Rs {product.get('price'):,}
User's exact words: "{user_input_raw}"
Situation: {context.get('detected_event', 'general purchase')}
{context_block}
User budget: Rs {context.get('budget', 'not specified')}

Agent verdicts:
{debate_lines}

Confidence score computed: {final_score:.0f}%

Rules for your response:
- Sentence 1: State the core tradeoff in context of WHO this person is and WHY they are buying (e.g. "For a winter trek to Kashmir, the waterproof durability of this bag outweighs the Rs 200 price concern from Paisa.")
- Sentence 2: State your recommendation clearly (e.g. "Buy with confidence — reliability and cultural fit matter more than marginal savings here.")
- Do not use bullet points or lists
- Write in warm, direct Indian English
- Do NOT repeat what the agents already said — synthesise with the human context
- Do NOT mention the confidence score number
- Reference the location/cultural context if it's relevant to the product choice"""

        response = _client.chat.completions.create(
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens_orchestrator,
            temperature=settings.llm_temperature,
            messages=[{"role": "user", "content": prompt}],
            timeout=20.0,
        )
        soch_message = response.choices[0].message.content.strip()

        # Final verdict: 2+ rejections → REJECT, otherwise RECOMMEND
        reject_count = verdicts.count("reject")
        final_verdict = "REJECT" if reject_count >= 2 else "RECOMMEND"

        return {
            "agent_name": self.name,
            "agent_role": self.role,
            "message": soch_message,
            "score_contribution": 0,
            "verdict": final_verdict,
            "final_score": final_score,
            "data": {
                "reject_count": reject_count,
                "total_contribution": total_contribution,
                "cultural_context_used": cultural_context,
                "location_context_used": location_context,
            },
        }
