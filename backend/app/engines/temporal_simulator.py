"""
temporal_simulator.py — Generates three purchase timing strategies for the user.

WHY THREE STRATEGIES:
Indian buyers often delay purchases hoping for a sale, or split across payment cycles.
This engine models three real alternatives — Buy Now, Wait for Sale, Split Purchase —
computes their actual prices using configured discount rates, and flags when a
government scheme payment (e.g. PM Kisan) falls within the wait window.

The recommended strategy is computed deterministically:
- If urgency_days < 5: always recommend Buy Now (no time to wait).
- If waiting saves > 15% of base price: recommend Wait.
- Otherwise: recommend Buy Now.

All rates and fractions come from app.config. Zero magic numbers in this file.

Library: json (stdlib), datetime (stdlib), app.config (internal).
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.config import settings

_CONTEXT_PATH = os.path.join(os.path.dirname(__file__), "../data/bharat_context.json")
_context_cache: Optional[Dict] = None


def _load_context() -> Dict:
    global _context_cache
    if _context_cache is None:
        with open(_CONTEXT_PATH, encoding="utf-8") as f:
            _context_cache = json.load(f)
    return _context_cache


def _check_upcoming_scheme(current_month: int) -> Optional[str]:
    """
    Checks if any government scheme payment falls within the next ~30 days.
    Returns a note string if yes, None if no.
    """
    context = _load_context()
    schemes = context.get("government_schemes", {})
    next_month = (current_month % 12) + 1

    for scheme_key, scheme in schemes.items():
        payment_months = scheme.get("payment_months", [])
        if current_month in payment_months or next_month in payment_months:
            target_month = current_month if current_month in payment_months else next_month
            month_name = datetime(2000, target_month, 1).strftime("%B")
            amount = scheme.get("average_amount_per_instalment", 0)
            name = scheme.get("name", scheme_key)
            return (
                f"A {name} payment of ~Rs {amount:,} is expected in {month_name}. "
                f"Waiting until then could help fund this purchase."
            )
    return None


def generate(
    product: Dict[str, Any],
    context: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Generates three TemporalStrategy objects for the given product and context.

    Args:
        product: Product dict from mock_products.json
        context: Dict with urgency_days, budget, detected_event, etc.

    Returns:
        List of 3 strategy dicts matching the TemporalStrategy Pydantic schema.
    """
    base_price: int = product.get("price", 0)
    urgency_days: int = context.get("urgency_days", 30)
    current_month: int = datetime.now().month

    # ── Compute strategy prices ────────────────────────────────────────────
    sale_price = int(base_price * settings.temporal_sale_discount)
    savings_wait = base_price - sale_price
    savings_pct = (savings_wait / base_price) * 100 if base_price > 0 else 0

    # Split: pay split_fraction now, remainder later
    split_now = int(base_price * settings.temporal_split_fraction)
    split_later = base_price - split_now

    # ── Timing labels ─────────────────────────────────────────────────────
    today = datetime.now()
    wait_date = today + timedelta(days=settings.temporal_wait_days)
    wait_label = wait_date.strftime("%d %b").lstrip("0") or wait_date.strftime("%d %b")

    # ── Government scheme check ───────────────────────────────────────────
    scheme_note = _check_upcoming_scheme(current_month)

    # ── Recommendation logic ──────────────────────────────────────────────
    if urgency_days < 5:
        # No time to wait — Buy Now wins
        buy_now_recommended = True
        wait_recommended = False
        split_recommended = False
        urgency_override = True
    elif savings_pct >= 15:
        # Saving more than 15% — Wait wins (if we have time)
        buy_now_recommended = False
        wait_recommended = True
        split_recommended = False
        urgency_override = False
    else:
        # Savings too small to justify waiting
        buy_now_recommended = True
        wait_recommended = False
        split_recommended = False
        urgency_override = False

    # ── Build strategy notes ──────────────────────────────────────────────
    buy_now_note = (
        f"Order today and receive in {product.get('delivery_days', 3)} days — "
        f"well before your {context.get('detected_event', 'event')}. "
        f"No discount, but zero risk of stockout or price increase."
    )

    if urgency_override:
        buy_now_note += " With only a few days to your event, this is the only safe choice."

    wait_note = (
        f"Waiting {settings.temporal_wait_days} days could save you Rs {savings_wait:,} "
        f"({savings_pct:.0f}% discount during a sale window). "
    )
    if scheme_note:
        wait_note += scheme_note
    elif urgency_days < settings.temporal_wait_days + product.get("delivery_days", 3):
        wait_note += (
            f"However, with your event in {urgency_days} days and delivery taking "
            f"{product.get('delivery_days', 3)} days, waiting is risky."
        )
    else:
        wait_note += f"You have enough time before your event to wait without risk."

    split_note = (
        f"Pay Rs {split_now:,} now to reserve the item (55% upfront), "
        f"then Rs {split_later:,} later using a buy-now-pay-later option. "
        f"Useful if your budget is tight this month."
    )

    strategies = [
        {
            "strategy_name": "Buy Now",
            "strategy_key": "buy_now",
            "price": base_price,
            "savings_vs_now": 0,
            "recommended": buy_now_recommended,
            "note": buy_now_note,
            "action_date": f"Order today — arrives in {product.get('delivery_days', 3)} days",
        },
        {
            "strategy_name": "Wait for Sale",
            "strategy_key": "wait",
            "price": sale_price,
            "savings_vs_now": savings_wait,
            "recommended": wait_recommended,
            "note": wait_note,
            "action_date": f"Wait until ~{wait_label} for sale window",
        },
        {
            "strategy_name": "Split Purchase",
            "strategy_key": "split",
            "price": base_price,
            "savings_vs_now": 0,
            "recommended": split_recommended,
            "note": split_note,
            "action_date": f"Pay Rs {split_now:,} now, Rs {split_later:,} next month",
        },
    ]

    return strategies
