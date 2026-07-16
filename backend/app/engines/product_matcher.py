"""
product_matcher.py — Filters and ranks mock products for a given life event and context.

WHY THIS MODULE EXISTS:
Product selection must be driven by the detected life event, Bharat context,
AND the user's specific cultural/climate needs — not just hardcoded event tags.
This engine reads mock_products.json, applies a three-stage pipeline:
  1. Category-based filter (from LLM-detected phases)
  2. Institution constraints (wattage, prohibited items)
  3. Budget filter
  4. Semantic trust scoring — boosts products that match LLM-extracted product_needs
     and cultural tags (e.g. "woolen", "trek", "thermal", "modest")

Libraries: json (stdlib), math (stdlib), app.config (internal).
"""

import json
import math
import os
from typing import List, Dict, Any, Optional

_PRODUCTS_PATH = os.path.join(os.path.dirname(__file__), "../data/mock_products.json")
_NEW_PRODUCTS_PATH = os.path.join(os.path.dirname(__file__), "../data/new_products_chunk.json")
_products_cache: Optional[List[Dict[str, Any]]] = None

def _load_products() -> List[Dict[str, Any]]:
    """Loads and merges product catalog once into a module-level cache."""
    global _products_cache
    if _products_cache is not None:
        return _products_cache
    with open(_PRODUCTS_PATH, encoding="utf-8") as f:
        products = json.load(f)
    # Merge the additional products chunk, deduplicating by product ID
    if os.path.exists(_NEW_PRODUCTS_PATH):
        with open(_NEW_PRODUCTS_PATH, encoding="utf-8") as f:
            new_products = json.load(f)
        existing_ids = {p.get("id") for p in products}
        products.extend([p for p in new_products if p.get("id") not in existing_ids])
    _products_cache = products
    return _products_cache


def _semantic_match_score(
    product: Dict[str, Any],
    exact_items: Optional[List[str]] = None,
    product_needs: Optional[List[str]] = None,
    cultural_keywords: Optional[List[str]] = None,
) -> float:
    """
    Composite relevance score combining:
    - Base trust score: seller_rating × log(reviews) - return_rate_penalty
    - Exact item boost: +1000 if product name/tags match what user literally asked for
    - Semantic needs boost: +200 per product_need phrase that overlaps with product
    - Cultural keyword boost: +150 per cultural/climate keyword matched
    
    This replaces the old _trust_score() which only had exact_items matching.
    """
    rating = product.get("seller_rating", 0.0)
    reviews = product.get("seller_review_count", 1)
    return_rate = product.get("seller_return_rate", 0.0)
    base_score = (rating * math.log1p(reviews)) - (return_rate * 0.5)

    name_lower = product.get("name", "").lower()
    tags_lower = [t.lower() for t in product.get("tags", [])]
    desc_lower = product.get("description", "").lower()
    product_text = name_lower + " " + " ".join(tags_lower) + " " + desc_lower
    product_words = set(product_text.replace("-", " ").replace("_", " ").split())

    # ── Exact items boost ──────────────────────────────────────────────────
    if exact_items:
        requested_words = set()
        for item in exact_items:
            for word in item.lower().split():
                if len(word) > 2 and word not in {"and", "the", "with", "small", "big", "a", "an", "some", "for"}:
                    requested_words.add(word)
        if requested_words.intersection(product_words):
            base_score += 1000.0

    # ── Semantic product needs boost ────────────────────────────────────────
    if product_needs:
        for need in product_needs:
            need_words = set(
                w for w in need.lower().replace("-", " ").split()
                if len(w) > 2 and w not in {"and", "the", "with", "for", "a", "an", "of", "to"}
            )
            overlap = need_words.intersection(product_words)
            if overlap:
                # More overlap = higher boost
                base_score += 200.0 * (len(overlap) / max(len(need_words), 1))

    # ── Cultural / climate keyword boost ────────────────────────────────────
    if cultural_keywords:
        for kw in cultural_keywords:
            kw_lower = kw.lower()
            if kw_lower in product_text:
                base_score += 150.0

    return base_score


def _extract_cultural_keywords(product_search_context: Optional[Dict]) -> List[str]:
    """
    Extracts searchable keywords from the LLM's cultural and climate context
    to boost culturally-relevant products.
    
    E.g. cultural_context about Kashmir → keywords: ["woolen", "thermal", "warm", "modest", "trek"]
    """
    if not product_search_context:
        return []

    keywords = []
    cultural = (product_search_context.get("cultural_context") or "").lower()
    climate = (product_search_context.get("climate_note") or "").lower()
    needs = product_search_context.get("product_needs", [])

    # Climate-derived keywords
    if any(w in climate for w in ["cold", "mountain", "snow", "winter", "alpine", "trek"]):
        keywords.extend(["woolen", "thermal", "warm", "fleece", "winter", "trek", "layered"])
    if any(w in climate for w in ["humid", "coastal", "tropical"]):
        keywords.extend(["cotton", "breathable", "moisture", "lightweight"])
    if any(w in climate for w in ["desert", "arid", "hot", "dust"]):
        keywords.extend(["dust-resistant", "cooling", "cotton", "lightweight"])

    # Cultural-derived keywords
    if any(w in cultural for w in ["islamic", "muslim", "modest"]):
        keywords.extend(["modest", "full-sleeve", "cotton", "traditional", "kurta"])
    if any(w in cultural for w in ["trek", "adventure", "outdoor", "hiking"]):
        keywords.extend(["trek", "outdoor", "waterproof", "durable", "backpack"])
    if any(w in cultural for w in ["wedding", "bridal", "festive", "occasion"]):
        keywords.extend(["silk", "traditional", "festive", "ethnic"])

    # Extract keywords from product needs
    for need in needs:
        words = [w for w in need.lower().split() if len(w) > 3]
        keywords.extend(words[:3])  # Take first 3 meaningful words from each need

    return list(set(keywords))


def match_products(
    event_key: str,
    institution_data: Optional[Dict] = None,
    budget: Optional[int] = None,
    pincode: str = "600001",
    limit: int = 5,
    categories: Optional[List[str]] = None,
    exact_items: Optional[List[str]] = None,
    suggested_items_with_categories: Optional[Dict[str, str]] = None,
    product_search_context: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    """
    Returns up to `limit` products relevant to the given life event,
    filtered by institution constraints and budget, ranked by semantic trust score.

    Args:
        event_key: Key from life_event_templates.json or LLM-detected event
        institution_data: Optional dict from bharat_context.json institutions block
        budget: Optional maximum price in INR
        pincode: User's pincode for reachability filter
        limit: Maximum number of products to return
        categories: LLM-detected relevant categories
        exact_items: Specific items the user literally asked for
        product_search_context: Dict with cultural_context, climate_note, product_needs
                                 from LLM detection for semantic scoring

    Returns:
        List of product dicts, sorted by semantic trust score descending.
    """
    products = _load_products()

    # ── Extract semantic context ───────────────────────────────────────────
    product_needs = []
    cultural_keywords = []
    if product_search_context:
        product_needs = product_search_context.get("product_needs", [])
        cultural_keywords = _extract_cultural_keywords(product_search_context)

    # ── 1. Filter by category (LLM-detected phases take priority) ─────────
    relevant = []
    if categories:
        relevant = [
            p for p in products
            if any(cat.lower() in p.get("category", "").lower() for cat in categories)
        ]

    # ── 2. Fallback: filter by event tag ──────────────────────────────────
    if not relevant:
        relevant = [p for p in products if event_key in p.get("event_tags", [])]

    # ── 3. Last resort: all products (scored and filtered below) ──────────
    if not relevant:
        relevant = list(products)

    # ── 4. Apply institution constraints ──────────────────────────────────
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

    # ── 5. Filter by budget ────────────────────────────────────────────────
    if budget and budget > 0:
        relevant = [p for p in relevant if p.get("price", 0) <= budget]

    # ── 6. Rank by semantic trust score ───────────────────────────────────
    relevant.sort(
        key=lambda x: _semantic_match_score(
            x,
            exact_items=exact_items,
            product_needs=product_needs,
            cultural_keywords=cultural_keywords,
        ),
        reverse=True
    )

    final_products = relevant[:limit]

    # ── 7. Product Gap Handling (Out of Stock cards) ──────────────────────
    items_to_check = []
    if exact_items:
        items_to_check.extend([(item, categories[0] if categories else "generic") for item in exact_items])
    if suggested_items_with_categories:
        items_to_check.extend([(item, cat) for item, cat in suggested_items_with_categories.items()])

    if items_to_check:
        # Process in reverse so the first unmatched item ends up at the very top when we insert(0)
        for item, item_cat in reversed(items_to_check):
            item_words = set(w for w in item.lower().split() if len(w) > 3)
            if not item_words:
                item_words = set(item.lower().split())

            matched = False
            
            # Strip common adjectives to ensure we match the core noun
            core_words = item_words - {"waterproof", "travel", "portable", "quick", "dry", "action", "smart", "electric", "digital", "mini"}
            if not core_words:
                core_words = item_words

            for p in final_products:
                p_text = (p.get("name", "") + " " + " ".join(p.get("tags", [])) + " " + p.get("description", "")).lower()
                p_words = set(p_text.replace("-", " ").replace("_", " ").split())
                
                # If there is meaningful overlap on core nouns, consider it satisfied
                if core_words.intersection(p_words):
                    matched = True
                    break
            
            if not matched:
                # Generate an out of stock card and prepend it
                dummy_product = {
                    "id": f"OOS_{item.replace(' ', '_').upper()}",
                    "name": item.title(),
                    "price": 0,
                    "original_price": 0,
                    "discount_percent": 0,
                    "category": item_cat,
                    "image_url": "https://placehold.co/400x400/eeeeee/999999?text=Out+of+Stock",
                    "seller_name": "PRISM Catalog",
                    "seller_rating": 0.0,
                    "seller_review_count": 0,
                    "seller_return_rate": 0.0,
                    "trust_score": 0.0,
                    "tags": [item],
                    "stock_status": "out_of_stock",
                }
                final_products.insert(0, dummy_product)

    return final_products[:limit]
