"""
paisa.py — Paisa Budget Agent for PRISM.

ROLE: Evaluates whether the product price fits the user's budget and whether
the price trend makes now a good or bad time to buy.

WHY DETERMINISTIC (no LLM):
Budget evaluation is a numeric comparison — price vs budget, trend vs thresholds.
Deterministic rules give instantly auditable, reproducible verdicts.

All thresholds come from app.config (imported from .env). Zero magic numbers
in this file.

Library: app.config (internal), app.agents.base_agent (internal).
"""

from app.agents.base_agent import BaseAgent
from app.config import settings
from typing import Dict, Any, Optional


class PaisaBudgetAgent(BaseAgent):
    name = "Paisa"
    role = "Budget Agent"
    personality = (
        "Sharp and practical. Paisa watches every rupee and knows exactly "
        "when a deal is good and when you're being overcharged."
    )

    def evaluate(self, product: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        price: int = product.get("price", 0)
        price_trend: float = product.get("price_trend_7d", 0.0)
        budget: Optional[int] = context.get("budget")
        product_name = product.get("name", "this product")

        score = 0.0
        flags = []
        verdict = "approve"

        # ── Budget check ──────────────────────────────────────────────────
        if budget and budget > 0:
            if price > budget:
                overage = price - budget
                score += settings.budget_score_over_budget
                budget_note = (
                    f"Rs {price:,} is Rs {overage:,} over the stated budget of Rs {budget:,}."
                )
                flags.append(f"Rs {overage:,} over budget")
                verdict = "reject"
            else:
                headroom = budget - price
                budget_note = (
                    f"Rs {price:,} is within budget. Rs {headroom:,} budget remaining."
                )
        else:
            budget_note = f"Priced at Rs {price:,}. No budget cap was set by the user."

        # ── Price trend ───────────────────────────────────────────────────
        if price_trend > settings.budget_price_trend_high:
            score += settings.budget_score_rising
            trend_note = (
                f"Price has risen {price_trend:+.1f}% in the last 7 days — buying now "
                f"means buying at a recent high."
            )
            flags.append("price trending up")
            if verdict == "approve":
                verdict = "caution"
        elif price_trend < settings.budget_price_trend_low:
            score += settings.budget_score_falling
            trend_note = (
                f"Price has dropped {abs(price_trend):.1f}% in the last 7 days — "
                f"this is a good time to buy."
            )
            if verdict == "approve":
                verdict = "strong_approve"
        else:
            score += settings.budget_score_stable
            trend_note = (
                f"Price has been stable ({price_trend:+.1f}% change in 7 days). "
                f"No urgency to rush or delay."
            )

        # ── Build message ─────────────────────────────────────────────────
        if flags:
            flag_text = f" Watch out: {', '.join(flags)}."
        else:
            flag_text = " No budget red flags."

        message = f"{budget_note} {trend_note}{flag_text}"

        return self._build_result(
            message=message,
            score=score,
            verdict=verdict,
            data={
                "price": price,
                "budget": budget,
                "price_trend_7d": price_trend,
                "flags": flags,
            },
        )
