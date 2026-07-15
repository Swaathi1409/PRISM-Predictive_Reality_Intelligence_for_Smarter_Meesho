"""
kismat.py — Kismat Trust Agent for PRISM.

WHAT CHANGED FROM v1:
The previous version only checked seller_rating, seller_return_rate, and review_count
against numeric thresholds from settings. It had no awareness of:
- Whether the product was culturally appropriate for the user's context
- Whether the product suited the detected season or climate
- Whether the product matched the user's stated purpose

This version receives the full Bharat context bundle and uses it in its evaluation
message. The numeric scoring stays rule-based (fast, deterministic) but the message
now explains the verdict in cultural terms when relevant.

Libraries: app.config (internal), app.agents.base_agent (internal).
"""

from app.agents.base_agent import BaseAgent
from app.config import settings
from typing import Dict, Any


class KismatTrustAgent(BaseAgent):
    name = "Kismat"
    role = "Trust Agent"
    personality = "Vigilant. Protects the user from bad sellers and culturally mismatched products."

    def evaluate(self, product: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        rating = product.get("seller_rating", 0)
        reviews = product.get("seller_review_count", 0)
        return_rate = product.get("seller_return_rate", 0)
        stock = product.get("stock_status", "in_stock")
        tags = product.get("tags", [])

        # Cultural fit check — uses context bundle
        cultural_context = context.get("cultural_context", [])
        travel_purpose = context.get("travel_purpose")
        season = context.get("season")
        event_key = context.get("event_key", "general")

        score = 0
        flags = []
        approvals = []

        # Seller trust scoring
        if rating >= settings.trust_good_rating_min:
            score += settings.trust_score_good
            approvals.append(f"{rating}★ over {reviews:,} orders")
        elif rating >= 3.5:
            score += settings.trust_score_medium
            flags.append(f"seller rating only {rating}★")
        else:
            score += settings.trust_score_bad
            flags.append(f"low seller rating {rating}★")

        if return_rate > settings.trust_high_return_rate:
            score += settings.trust_score_bad
            flags.append(f"{return_rate}% return rate is high")
        elif return_rate > settings.trust_medium_return_rate:
            score += settings.trust_score_medium
            flags.append(f"{return_rate}% return rate, moderate risk")
        else:
            score += 5
            approvals.append(f"low {return_rate}% return rate")

        if stock == "low_stock":
            score -= 5
            flags.append("stock running low — availability risk")
        elif stock == "out_of_stock":
            score -= 20
            flags.append("out of stock")

        # Cultural fit scoring
        cultural_flag = _check_cultural_fit(tags, cultural_context, travel_purpose, season, event_key)
        if cultural_flag:
            score -= 10
            flags.append(cultural_flag)

        # Build message
        if flags and approvals:
            message = f"Approved seller ({'; '.join(approvals)}) but flagging: {'; '.join(flags)}."
        elif flags:
            message = f"Flagging concerns: {'; '.join(flags)}."
        else:
            message = f"Seller looks trustworthy. {'; '.join(approvals)}."

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
                "seller_rating": rating,
                "review_count": reviews,
                "return_rate": return_rate,
                "stock_status": stock,
                "cultural_fit_flag": cultural_flag,
                "cultural_context_used": cultural_context
            }
        )


def _check_cultural_fit(tags, cultural_context, travel_purpose, season, event_key) -> str:
    """
    Returns a flag message if the product is a poor cultural or contextual fit,
    or empty string if it fits well.
    """
    tag_str = " ".join(tags).lower()

    if "kashmir_muslim_majority" in cultural_context:
        if any(w in tag_str for w in ["sleeveless", "shorts", "bikini", "revealing"]):
            return "not appropriate for conservative dress norms in Kashmir"

    if travel_purpose == "trek" and season == "winter":
        if "synthetic" in tag_str and "warm" not in tag_str and "thermal" not in tag_str:
            return "synthetic fabric without thermal properties — poor for winter trek"

    if "coastal_region" in cultural_context:
        if "wool" in tag_str and "summer" in tag_str:
            return "wool in coastal region may be unsuitable for humid climate"

    if event_key == "wedding":
        if any(w in tag_str for w in ["casual", "western", "office"]):
            return "product category does not align with wedding occasion"

    return ""
