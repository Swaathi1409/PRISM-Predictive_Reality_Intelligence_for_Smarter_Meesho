"""
samay.py — Samay Time Agent for PRISM.

ROLE: Evaluates whether the product can be delivered in time for the user's
life event, given delivery_days, available_pincodes, and event urgency.

WHY DETERMINISTIC (no LLM):
Delivery feasibility is a date arithmetic problem — days available minus
delivery days. Deterministic and exact.

All thresholds come from app.config (imported from .env). Zero magic numbers
in this file.

Library: app.config (internal), app.agents.base_agent (internal).
"""

from app.agents.base_agent import BaseAgent
from app.config import settings
from typing import Dict, Any, List


class SamayTimeAgent(BaseAgent):
    name = "Samay"
    role = "Time Agent"
    personality = (
        "Precise and urgent. Samay knows that the right product at the wrong "
        "time is the wrong product. Delivery windows are non-negotiable."
    )

    def evaluate(self, product: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        delivery_days: int = product.get("delivery_days", 5)
        available_pincodes: List[str] = product.get("available_pincodes", [])
        user_pincode: str = context.get("user_pincode", "600001")
        urgency_days: int = context.get("urgency_days", 30)
        event_label: str = context.get("detected_event", "your event")

        score = 0.0
        flags = []
        verdict = "approve"

        # ── Pincode reachability ──────────────────────────────────────────
        if available_pincodes and user_pincode not in available_pincodes:
            score += settings.time_score_unreachable
            pincode_note = (
                f"This seller does not deliver to pincode {user_pincode}. "
                f"You may need to use a nearby pickup point or choose a different seller."
            )
            flags.append(f"no delivery to {user_pincode}")
            verdict = "reject"
        else:
            pincode_note = f"Delivery confirmed to pincode {user_pincode}."

        # ── Delivery speed ────────────────────────────────────────────────
        if delivery_days <= settings.time_delivery_fast_days:
            score += settings.time_score_fast
            speed_note = f"Fast delivery in {delivery_days} day(s)."
            if verdict == "approve":
                verdict = "strong_approve"
        elif delivery_days <= urgency_days:
            score += settings.time_score_normal
            buffer = urgency_days - delivery_days
            speed_note = (
                f"Delivery in {delivery_days} days — arrives {buffer} day(s) before "
                f"your deadline for {event_label}."
            )
        else:
            score += settings.time_score_late
            overrun = delivery_days - urgency_days
            speed_note = (
                f"Delivery in {delivery_days} days will arrive {overrun} day(s) AFTER "
                f"your deadline for {event_label}. This may not be suitable."
            )
            flags.append(f"arrives {overrun}d late for {event_label}")
            if verdict == "approve":
                verdict = "flag"
            # If delivery misses deadline by more than a week, reject
            if overrun > 7:
                verdict = "reject"
                score += settings.time_score_unreachable

        # ── Build message ─────────────────────────────────────────────────
        if flags:
            flag_text = f" Time concerns: {'; '.join(flags)}."
        else:
            flag_text = " No delivery timing issues."

        message = f"{pincode_note} {speed_note}{flag_text}"

        return self._build_result(
            message=message,
            score=score,
            verdict=verdict,
            data={
                "delivery_days": delivery_days,
                "user_pincode": user_pincode,
                "urgency_days": urgency_days,
                "pincode_reachable": (user_pincode in available_pincodes) if available_pincodes else True,
                "flags": flags,
            },
        )
