"""
samay.py — Samay Time Agent for PRISM.

WHAT CHANGED FROM v1:
Now uses urgency_days from the LLM-parsed event (instead of a hardcoded field)
and factors in whether the pincode is reachable from the product's available areas.

Libraries: app.config (internal), app.agents.base_agent (internal).
"""

from app.agents.base_agent import BaseAgent
from app.config import settings
from typing import Dict, Any


class SamayTimeAgent(BaseAgent):
    name = "Samay"
    role = "Time Agent"
    personality = "Precise. Cares about whether the product actually arrives in time."

    def evaluate(self, product: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        delivery_days = product.get("delivery_days", 5)
        urgency_days = context.get("urgency_days")  # from LLM parser
        pincode = context.get("user_pincode", "")
        available_pincodes = product.get("available_pincodes", [])

        score = 0
        message_parts = []

        # Pincode reachability
        pincode_ok = not available_pincodes or pincode in available_pincodes
        if not pincode_ok:
            score += settings.time_score_unreachable
            message_parts.append(f"delivery not confirmed for pincode {pincode}")
        else:
            score += 3
            message_parts.append(f"delivery confirmed for your pincode")

        # Delivery speed vs urgency
        if urgency_days is not None:
            buffer = urgency_days - delivery_days
            if buffer < 0:
                score += settings.time_score_late
                message_parts.append(f"arrives in {delivery_days}d but event is in {urgency_days}d — too late")
            elif buffer < 2:
                score += 0
                message_parts.append(f"tight window — {delivery_days}d delivery, event in {urgency_days}d")
            elif delivery_days <= settings.time_delivery_fast_days:
                score += settings.time_score_fast
                message_parts.append(f"fast {delivery_days}d delivery, {buffer}d buffer before event")
            else:
                score += settings.time_score_normal
                message_parts.append(f"{delivery_days}d delivery with {buffer}d to spare")
        else:
            # No urgency known — just score on raw speed
            if delivery_days <= settings.time_delivery_fast_days:
                score += settings.time_score_fast
                message_parts.append(f"fast {delivery_days}d delivery")
            else:
                score += settings.time_score_normal
                message_parts.append(f"standard {delivery_days}d delivery")

        message = f"Samay check: {'; '.join(message_parts)}."

        if score >= settings.time_score_fast:
            verdict = "approve"
        elif score >= 0:
            verdict = "caution"
        elif score >= settings.time_score_late:
            verdict = "flag"
        else:
            verdict = "reject"

        return self._build_result(
            message=message,
            score=float(score),
            verdict=verdict,
            data={
                "delivery_days": delivery_days,
                "urgency_days": urgency_days,
                "pincode": pincode,
                "pincode_reachable": pincode_ok
            }
        )
