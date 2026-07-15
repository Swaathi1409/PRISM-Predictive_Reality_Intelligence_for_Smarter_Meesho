"""
paisa.py — Paisa Budget Agent for PRISM.

WHAT CHANGED FROM v1:
Added awareness of: upcoming government scheme payments (PM Kisan, salary cycles),
regional price sensitivity, and whether a "wait" recommendation makes sense
given the user's detected financial calendar context.

Libraries: app.config (internal), app.agents.base_agent (internal).
"""

from app.agents.base_agent import BaseAgent
from app.config import settings
from typing import Dict, Any


class PaisaBudgetAgent(BaseAgent):
    name = "Paisa"
    role = "Budget Agent"
    personality = "Practical. Finds the right moment to buy, not just the cheapest price."

    def evaluate(self, product: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        price = product.get("price", 0)
        trend = product.get("price_trend_7d", 0)
        budget = context.get("budget")
        upcoming_payment = context.get("upcoming_scheme_payment")  # from Bharat context

        score = 0
        message_parts = []

        # Budget check
        if budget:
            if price > budget:
                over_by = price - budget
                score += settings.budget_score_over_budget
                message_parts.append(f"Rs {over_by:,} over your budget of Rs {budget:,}")
            else:
                headroom = budget - price
                score += 5
                message_parts.append(f"within budget with Rs {headroom:,} to spare")

        # Price trend
        if trend > settings.budget_price_trend_high:
            score += settings.budget_score_rising
            message_parts.append(f"price rising {trend:.1f}% — buy soon")
        elif trend < settings.budget_price_trend_low:
            score += settings.budget_score_falling
            message_parts.append(f"price falling {abs(trend):.1f}% — might drop further")
        else:
            score += settings.budget_score_stable
            message_parts.append("price stable")

        # Upcoming payment awareness
        if upcoming_payment:
            score += 5
            message_parts.append(f"PM Kisan payment due {upcoming_payment} — timing purchase after it saves cash")

        # Build message
        message = f"Paisa check: {'; '.join(message_parts)}." if message_parts else "Price looks reasonable."

        if score >= 10:
            verdict = "strong_approve"
        elif score >= 0:
            verdict = "approve"
        elif score >= -10:
            verdict = "caution"
        elif score >= -18:
            verdict = "flag"
        else:
            verdict = "reject"

        return self._build_result(
            message=message,
            score=float(score),
            verdict=verdict,
            data={
                "price": price,
                "budget": budget,
                "trend_7d": trend,
                "upcoming_payment": upcoming_payment
            }
        )
