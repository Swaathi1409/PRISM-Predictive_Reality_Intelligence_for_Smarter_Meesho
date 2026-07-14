"""
product_matcher.py — Filters and ranks mock products for a given life event and context.

WHY THIS MODULE EXISTS:
Product selection must be driven by the detected life event and Bharat context,
not hardcoded product IDs. This engine reads mock_products.json, filters by event
relevance, applies institution constraints (wattage limits, prohibited items),
sorts by seller trust score, and returns the top 5 candidates for agent evaluation.

Libraries: json (stdlib), math (stdlib), app.config (internal).
License: N/A (stdlib only).
"""

import json
import math
import os
from typing import List, Dict, Any, Optional

_PRODUCTS_PATH = os.path.join(os.path.dirname(__file__), "../data/mock_products.json")
_products_cache: Optional[List[Dict[str, Any]]] = None


def _load_products() -> List[Dict[str, Any]]:
    global _products_cache
    if _products_cache is None:
        with open(_PRODUCTS_PATH, encoding="utf-8") as f:
            _products_cache = json.load(f)
    return _products_cache


def _trust_score(p: Dict[str, Any]) -> float:
    """Composite seller trust score: rating × log(reviews) - return_rate_penalty."""
    rating = p.get("seller_rating", 0.0)
    reviews = p.get("seller_review_count", 1)
    return_rate = p.get("seller_return_rate", 0.0)
    return (rating * math.log1p(reviews)) - (return_rate * 0.5)


def match_products(
    event_key: str,
    institution_data: Optional[Dict] = None,
    budget: Optional[int] = None,
    pincode: str = "600001",
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Returns up to `limit` products relevant to the given life event,
    filtered by institution constraints and budget, ranked by seller trust.

    Args:
        event_key: Key from life_event_templates.json (e.g. 'hostel_move')
        institution_data: Optional dict from bharat_context.json institutions block
        budget: Optional maximum price in INR
        pincode: User's pincode for reachability filter
        limit: Maximum number of products to return

    Returns:
        List of product dicts, sorted by trust score descending.
    """
    products = _load_products()

    # 1. Filter by event relevance
    relevant = [p for p in products if event_key in p.get("event_tags", [])]
    if not relevant:
        relevant = list(products)  # fallback: all products

    # 2. Filter by institution constraints
    if institution_data:
        wattage_limit = institution_data.get("appliance_wattage_limit")
        prohibited = institution_data.get("prohibited_items", [])

        if wattage_limit:
            relevant = [
                p for p in relevant
                if p.get("wattage") is None or p.get("wattage", 0) <= wattage_limit
            ]

        if prohibited:
            relevant = [
                p for p in relevant
                if not any(
                    proh.replace("_", " ").lower() in p.get("name", "").lower()
                    for proh in prohibited
                )
            ]

    # 3. Filter by budget
    if budget and budget > 0:
        budget_filtered = [p for p in relevant if p.get("price", 0) <= budget]
        if budget_filtered:
            relevant = budget_filtered

    # 4. Filter by pincode reachability
    pincode_available = [
        p for p in relevant
        if pincode in p.get("available_pincodes", []) or not p.get("available_pincodes")
    ]
    if pincode_available:
        relevant = pincode_available

    # 5. Filter out of stock items
    in_stock = [p for p in relevant if p.get("stock_status") != "out_of_stock"]
    if in_stock:
        relevant = in_stock

    # 6. Rank by composite trust score
    relevant.sort(key=_trust_score, reverse=True)
    return relevant[:limit]
