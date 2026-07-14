"""
kismat.py — Kismat Trust Agent for PRISM.

ROLE: Evaluates seller trustworthiness based on rating, review count, return rate,
and stock status. Returns a score contribution that feeds the confidence genome.

WHY DETERMINISTIC (no LLM):
Trust evaluation is purely numeric — rating thresholds, return rate comparisons,
review volume. Deterministic rules are faster, cheaper, and more auditable than
an LLM for this task.

All thresholds come from app.config (imported from .env). Zero magic numbers
in this file.

Library: app.config (internal), app.agents.base_agent (internal).
"""

from app.agents.base_agent import BaseAgent
from app.config import settings
from typing import Dict, Any


class KismatTrustAgent(BaseAgent):
    name = "Kismat"
    role = "Trust Agent"
    personality = (
        "Cautious and thorough. Kismat has seen too many fake sellers "
        "and always checks the numbers before trusting anyone."
    )

    def evaluate(self, product: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        rating = product.get("seller_rating", 0.0)
        reviews = product.get("seller_review_count", 0)
        return_rate = product.get("seller_return_rate", 0.0)
        stock_status = product.get("stock_status", "in_stock")
        seller_name = product.get("seller_name", "this seller")

        score = 0.0
        flags = []

        # ── Rating evaluation ──────────────────────────────────────────────
        if rating >= settings.trust_good_rating_min:
            score += settings.trust_score_good
            rating_note = f"strong {rating:.1f}★ rating"
        elif rating >= settings.trust_good_rating_min - 1.0:
            score += settings.trust_score_medium
            rating_note = f"moderate {rating:.1f}★ rating"
            flags.append("average rating")
        else:
            score += settings.trust_score_bad
            rating_note = f"concerning {rating:.1f}★ rating"
            flags.append("low rating")

        # ── Review volume ─────────────────────────────────────────────────
        if reviews >= 1000:
            review_note = f"{reviews:,} verified reviews"
        elif reviews >= 100:
            review_note = f"{reviews} reviews (acceptable)"
            flags.append("limited review volume")
        else:
            score -= 5
            review_note = f"only {reviews} reviews — very low data"
            flags.append("very few reviews")

        # ── Return rate ───────────────────────────────────────────────────
        if return_rate >= settings.trust_high_return_rate:
            score += settings.trust_score_bad
            return_note = f"high return rate of {return_rate}% — serious concern"
            flags.append("high return rate")
            verdict = "reject"
        elif return_rate >= settings.trust_medium_return_rate:
            score += settings.trust_score_medium
            return_note = f"elevated return rate of {return_rate}%"
            flags.append("elevated return rate")
            verdict = "caution"
        else:
            score += 5
            return_note = f"low return rate of {return_rate}%"
            verdict = "approve"

        # ── Stock status ──────────────────────────────────────────────────
        stock_note = ""
        if stock_status == "low_stock":
            score -= 3
            stock_note = " Stock is running low — order soon to avoid disappointment."
            if verdict == "approve":
                verdict = "caution"
        elif stock_status == "out_of_stock":
            score -= 10
            stock_note = " This item is currently out of stock."
            verdict = "reject"

        # ── Override to strong_approve if all signals are excellent ───────
        if (
            rating >= settings.trust_good_rating_min
            and return_rate < settings.trust_medium_return_rate
            and reviews >= 1000
            and stock_status == "in_stock"
            and verdict == "approve"
        ):
            verdict = "strong_approve"

        # ── Build message ─────────────────────────────────────────────────
        if flags:
            flag_text = f" Concerns noted: {', '.join(flags)}."
        else:
            flag_text = " All trust signals look clean."

        message = (
            f"{seller_name} has a {rating_note}, {review_note}, and a {return_note}."
            f"{flag_text}{stock_note}"
        )

        return self._build_result(
            message=message,
            score=score,
            verdict=verdict,
            data={
                "seller_rating": rating,
                "seller_review_count": reviews,
                "seller_return_rate": return_rate,
                "stock_status": stock_status,
                "flags": flags,
            },
        )
