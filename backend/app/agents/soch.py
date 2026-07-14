"""
soch.py — Soch Orchestrator Agent for PRISM.

WHY THIS AGENT CALLS THE LLM (Groq, Apache 2.0):
The three specialist agents (Kismat, Paisa, Samay) use deterministic rule-based
logic — no LLM needed there because their verdicts are based on numeric thresholds.
Soch's job is different: it must synthesise potentially conflicting verdicts,
identify the real tradeoff in plain language, and make a final recommendation.
This is a reasoning task that benefits from LLM capability. Using the LLM only
here keeps costs low (one call per analysis) while putting LLM reasoning exactly
where it adds the most value.

Library: groq (Apache 2.0) — chosen for fast inference with OpenAI-compatible API.
License: Groq Terms.
app.config (internal), app.agents.base_agent (internal).
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
        "Listens to all agents, identifies the real tradeoff, "
        "makes the final call with full reasoning."
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
        Synthesises the three specialist agent verdicts, calls Claude once
        to produce a 2-sentence final verdict, and computes the final score.
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

        prompt = f"""You are Soch, the orchestrator of PRISM — an AI commerce recommendation system built for India.

Three specialist agents have evaluated a product for a user. Read their analysis carefully, identify the single most important tradeoff, and deliver your final verdict in exactly 2 sentences.

Product: {product.get('name')} at Rs {product.get('price'):,}
User situation: {context.get('detected_event', 'general purchase')} in {context.get('state', 'India')}
User budget: Rs {context.get('budget', 'not specified')}

Agent verdicts:
{debate_lines}

Confidence score computed: {final_score:.0f}%

Rules for your response:
- Sentence 1: State the core tradeoff in plain language (e.g. "The Rs 400 saving does not justify the 14% return risk given this pincode's drop-off distance.")
- Sentence 2: State your recommendation clearly (e.g. "I recommend this seller — reliability matters more than marginal savings here.")
- Do not use bullet points or lists
- Write in warm, direct Indian English
- Do not repeat what the agents already said — synthesise it
- Do not mention the confidence score number"""

        response = _client.chat.completions.create(
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens_orchestrator,
            temperature=settings.llm_temperature,
            messages=[{"role": "user", "content": prompt}],
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
            },
        }
