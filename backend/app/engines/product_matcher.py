"""
product_matcher.py — Filters and ranks products from SQLite catalog for a given life event.

WHY THIS MODULE EXISTS:
Product selection must be driven by the detected life event, Bharat context,
AND the user's specific cultural/climate needs — not just hardcoded event tags.
This engine reads prism_catalog.db (SQLite), applies a four-stage pipeline:
  1. Category-based filter (from LLM-detected phases)
  2. Institution constraints (wattage, prohibited items)
  3. Budget filter
  4. Semantic trust scoring — boosts products matching LLM-extracted product_needs
     and cultural tags (e.g. "woolen", "trek", "thermal", "modest")

TWO-TIER OUTPUT:
  top_picks    — best 1 product per subcategory (selected by composite 4-agent score).
                 Guarantees product variety: no two "top picks" are from the same subcategory.
  other_products — remaining scored products for the "More to Explore" row.

Fallback: if SQLite DB not found, loads from legacy JSON files.

Libraries: json (stdlib), math (stdlib), sqlite3 (stdlib), app.config (internal).
"""

import json
import math
import os
import sqlite3
from typing import List, Dict, Any, Optional

_DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
_DB_PATH = os.path.join(_DATA_DIR, "prism_catalog.db")

# Legacy JSON fallbacks (used if SQLite DB not found)
_PRODUCTS_PATH = os.path.join(_DATA_DIR, "mock_products.json")
_NEW_PRODUCTS_PATH = os.path.join(_DATA_DIR, "new_products_chunk.json")
_ENRICHED_V2_PATH = os.path.join(_DATA_DIR, "enriched_products_v2.json")

_products_cache: Optional[List[Dict[str, Any]]] = None

# ── Event-aware subcategory blocklist ─────────────────────────────────────────
# Prevents contextually irrelevant products from appearing even if they share
# a parent category. E.g. hostel_move uses "bedding" but baby bedding products
# should never appear in a hostel context.
EVENT_SUBCATEGORY_BLOCKLIST: Dict[str, set] = {
    "hostel_move": {
        "baby", "baby_products", "feeding_bottle", "sterilizer", "diaper",
        "baby_care", "stroller", "pram", "baby_food", "nursing", "nappy",
        "baby_bedding", "baby_mat", "baby_pillow",
        "wedding_apparel", "bridal", "lehenga", "sherwani",
        "toys_games", "board_games",
        "pet_supplies", "pet_food",
        "power_tools", "drill", "automotive",
        # High-wattage kitchen appliances are not allowed in most hostels (1000W limit)
        # Mini kettles belong to kitchen_essentials, not kitchen_appliances
        "kitchen_appliances", "air_cooler", "ceiling_fan",
    },
    "first_job": {
        "baby", "baby_products", "feeding_bottle", "diaper", "baby_care",
        "toys_games", "kids_toys", "stroller",
        "pet_supplies",
    },
    "government_exam": {
        "baby", "baby_products", "wedding_apparel", "toys_games",
        "pet_supplies", "festival_decor", "automotive",
    },
    "new_baby": {
        "exam_supplies", "shop_supplies", "automotive", "power_tools",
    },
    "wedding": {
        "baby", "baby_products", "exam_supplies", "power_tools",
        "pet_supplies", "shop_supplies",
    },
    "festival_prep": {
        "baby", "baby_products", "exam_supplies", "shop_supplies",
        "power_tools", "automotive",
    },
    "travel_adventure": {
        "baby", "baby_products", "wedding_apparel", "exam_supplies",
        "shop_supplies", "power_tools",
    },
    "new_home": {
        "baby", "baby_products", "exam_supplies", "shop_supplies",
    },
    "shop_opening": {
        "baby", "baby_products", "toys_games", "wedding_apparel",
    },
    "religious_travel": {
        "shoes", "footwear", "slippers", "sneakers", "sandals", 
        "baby", "baby_products", "power_tools", "exam_supplies"
    },
    # generic is used for studio, creative workspace, photo studio etc.
    # Bedding/kitchen/baby items must never appear for these setups.
    "generic": {
        "baby", "baby_products", "feeding_bottle", "diaper", "nappy",
        "wedding_apparel", "bridal", "exam_supplies", "toys_games",
    },
}


# ── Subcategory relevance for exact-item queries ───────────────────────────────
# When a user asks for a specific item, only products from matching subcategories
# are boosted. Products from clearly wrong subcategories get a large penalty.
SUBCATEGORY_RELEVANCE: Dict[str, Dict[str, float]] = {
    # electronics exact terms → relevant subcategories
    "phone": {"smartphones": 800.0, "mobile": 800.0, "mobile_phones": 800.0},
    "mobile": {"smartphones": 800.0, "mobile_phones": 800.0},
    "laptop": {"laptops": 800.0, "computers": 600.0},
    "earphone": {"earphones": 800.0, "headphones": 600.0, "earbuds": 800.0},
    "headphone": {"headphones": 800.0, "earphones": 600.0},
    "charger": {"chargers": 800.0, "power_bank": 500.0},
    "powerbank": {"power_bank": 800.0, "chargers": 400.0},
    "speaker": {"speakers": 800.0, "home_audio": 600.0},
    "watch": {"watches": 800.0, "smartwatch": 800.0},
    "tablet": {"tablets": 800.0, "laptops": 400.0},
    "camera": {"cameras": 800.0, "security": 300.0},
    "printer": {"printers": 800.0},
    "router": {"networking": 800.0, "electronics": 400.0},
}

# ── Accessory categories for specific-product asks ────────────────────────────
# When user asks for a specific item (e.g. "I need a phone"), we show:
#   Row 1 → the exact item (or OOS stub)
#   Row 2 → "You may also need after buying your phone" → these accessory categories
ACCESSORY_CATEGORIES: Dict[str, List[str]] = {
    "phone":        ["electronics"],          # chargers, covers, cables
    "mobile":       ["electronics"],
    "smartphone":   ["electronics"],
    "laptop":       ["electronics", "bags_luggage", "stationery"],  # laptop bag, mouse, keyboard
    "earphone":     ["electronics"],
    "earphones":    ["electronics"],
    "headphone":    ["electronics"],
    "headphones":   ["electronics"],
    "charger":      ["electronics"],
    "powerbank":    ["electronics"],
    "power bank":   ["electronics"],
    "speaker":      ["electronics"],
    "tablet":       ["electronics", "bags_luggage"],
    "watch":        ["watches", "electronics"],
    "smartwatch":   ["electronics"],
    "camera":       ["electronics", "bags_luggage"],
    "tv":           ["electronics", "home_decor"],
    "television":   ["electronics", "home_decor"],
    "refrigerator": ["kitchen_appliances", "kitchen_essentials"],
    "fridge":       ["kitchen_appliances", "kitchen_essentials"],
    "washing machine": ["home_improvement"],
    "microwave":    ["kitchen_appliances", "kitchen_essentials"],
    "mixer":        ["kitchen_appliances", "kitchen_essentials"],
    "blender":      ["kitchen_appliances", "kitchen_essentials"],
    "ac":           ["home_improvement"],
    "air conditioner": ["home_improvement"],
}

# ── Accessory name-keyword filters ─────────────────────────────────────────────
# Products whose names contain these keywords are classified as accessories
# (not the primary item) for a given specific-ask keyword.
PRIMARY_SUBCATEGORIES: Dict[str, set] = {
    "phone":      {"smartphones", "mobile", "mobile_phones"},
    "mobile":     {"smartphones", "mobile_phones"},
    "smartphone": {"smartphones", "mobile_phones"},
    "laptop":     {"laptops", "computers"},
    "earphone":   {"earphones", "earbuds"},
    "earphones":  {"earphones", "earbuds"},
    "headphone":  {"headphones"},
    "headphones": {"headphones"},
    "charger":    {"chargers"},
    "powerbank":  {"power_bank"},
    "speaker":    {"speakers"},
    "watch":      {"watches", "smartwatch"},
    "smartwatch": {"smartwatch", "watches"},
    "tablet":     {"tablets"},
    "camera":     {"cameras"},
    "tv":         {"televisions", "tv", "television"},
    "television": {"televisions", "tv"},
}


def split_by_primary_and_accessories(
    products: List[Dict[str, Any]],
    primary_keyword: str,
) -> tuple:
    """
    Split a product list into (primary_products, accessory_products) for the
    specific-item two-tier display.

    primary_products  → products that ARE the item asked for (matched by subcategory)
    accessory_products → everything else (chargers, covers, cables, bags, etc.)

    Called by prism_service when is_specific_product_ask=True.
    """
    keyword = primary_keyword.lower().strip()
    primary_subcats = PRIMARY_SUBCATEGORIES.get(keyword, set())

    primary: List[Dict[str, Any]] = []
    accessories: List[Dict[str, Any]] = []

    for p in products:
        subcat = (p.get("subcategory") or "").lower()
        name_lower = (p.get("name") or "").lower()
        is_oos = p.get("stock_status") == "out_of_stock"

        # OOS stubs for the primary item always go to primary row
        if is_oos:
            primary.append(p)
            continue

        # Match by subcategory first
        if primary_subcats and subcat in primary_subcats:
            primary.append(p)
        # Keyword appears in name and subcategory is plausible
        elif keyword in name_lower and (not primary_subcats or subcat in primary_subcats):
            primary.append(p)
        else:
            accessories.append(p)

    return primary, accessories



# ── Name-phrase blocklist (catches products by actual name keywords) ────────────
# These are name substrings that indicate the product is contextually wrong
# for the event, regardless of what category/subcategory the CSV mapped it to.
EVENT_NAME_PHRASE_BLOCKLIST: Dict[str, set] = {
    "hostel_move": {
        "baby", "infant", "newborn", "new born", "neonatal", "nursery",
        "steriliz", "feeding bottle", "nipple", "pacifier", "nappy",
        "diaper", "pram", "stroller", "teether", "swaddle", "baby bib",
        "changing mat", "baby pillow", "baby blanket",
        # Appliances inappropriate for hostel (high-wattage, permanent fixtures)
        "ceiling fan", "air cooler", "steam iron", "dry iron", "washing machine",
        "refrigerator", "air conditioner", "geyser", "laundry basket",
    },
    "first_job": {
        "baby", "infant", "newborn", "diaper", "nappy", "pram", "stroller",
        "feeding bottle", "teether", "swaddle",
    },
    "government_exam": {
        "baby", "infant", "diaper", "pram", "stroller", "feeding bottle",
    },
    "wedding": {
        "baby", "infant", "diaper", "pram", "stroller", "feeding bottle",
    },
    "festival_prep": {
        "baby", "infant", "diaper", "pram", "stroller",
    },
    "travel_adventure": {
        "baby", "infant", "diaper", "pram", "stroller", "feeding bottle",
    },
    "new_home": {
        "baby pillow", "baby blanket", "baby bib",
    },
    "religious_travel": {
        "baby", "infant", "diaper", "slipper", "shoe", "footwear", "sneaker"
    },
    # generic is used for studio setups, creative workspaces etc.
    # Household/bedding items must never appear for these contexts.
    "generic": {
        "baby", "infant", "diaper",
        "harpic", "lizol", "domex", "toilet cleaner", "floor cleaner",
        "washing machine cleaner", "descaling",
        "comprehension skills", "short passages",
        "shirt stays", "shirt garters",
    },
}


def _row_to_product(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a SQLite Row to the product dict format used by the rest of PRISM."""
    p = dict(row)
    # Deserialize JSON TEXT columns back to Python lists
    for col in ("available_pincodes", "tags", "event_tags"):
        raw = p.get(col)
        if isinstance(raw, str):
            try:
                p[col] = json.loads(raw)
            except Exception:
                p[col] = []
    return p


def _load_products_from_sqlite() -> List[Dict[str, Any]]:
    """Load all products from SQLite DB into memory (cached)."""
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE stock_status = 'in_stock'")
    rows = cur.fetchall()
    conn.close()
    return [_row_to_product(r) for r in rows]


def _load_products_from_json() -> List[Dict[str, Any]]:
    """Legacy JSON fallback loader — used only if SQLite DB is missing."""
    products = []
    existing_ids: set = set()

    def _load(path):
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        return []

    for path in [_PRODUCTS_PATH, _NEW_PRODUCTS_PATH, _ENRICHED_V2_PATH]:
        for p in _load(path):
            pid = p.get("id")
            if pid and pid not in existing_ids:
                products.append(p)
                existing_ids.add(pid)

    return products


def _load_products() -> List[Dict[str, Any]]:
    """Loads product catalog once into module-level cache.

    Primary: SQLite DB (prism_catalog.db) — faster, indexed, ~1100+ products.
    Fallback: legacy JSON files — used if DB not built yet.
    """
    global _products_cache
    if _products_cache is not None:
        return _products_cache

    if os.path.exists(_DB_PATH):
        _products_cache = _load_products_from_sqlite()
    else:
        # Fallback to JSON files
        _products_cache = _load_products_from_json()

    return _products_cache


def invalidate_cache():
    """Call this after rebuilding the SQLite DB to force a reload."""
    global _products_cache
    _products_cache = None


def _semantic_match_score(
    product: Dict[str, Any],
    exact_items: Optional[List[str]] = None,
    product_needs: Optional[List[str]] = None,
    cultural_keywords: Optional[List[str]] = None,
) -> float:
    """
    Composite relevance score combining:
    - Base trust score: seller_rating x log(reviews) - return_rate_penalty
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
                if len(word) > 2 and word not in {
                    "and", "the", "with", "small", "big", "a", "an", "some", "for"
                }:
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

    E.g. cultural_context about Kashmir => keywords: ["woolen","thermal","warm","modest","trek"]
    """
    if not product_search_context:
        return []

    keywords = []
    cultural = (product_search_context.get("cultural_context") or "").lower()
    climate = (product_search_context.get("climate_note") or "").lower()
    needs = product_search_context.get("product_needs", [])

    if any(w in climate for w in ["cold", "mountain", "snow", "winter", "alpine", "trek"]):
        keywords.extend(["woolen", "thermal", "warm", "fleece", "winter", "trek", "layered"])
    if any(w in climate for w in ["humid", "coastal", "tropical"]):
        keywords.extend(["cotton", "breathable", "moisture", "lightweight"])
    if any(w in climate for w in ["desert", "arid", "hot", "dust"]):
        keywords.extend(["dust-resistant", "cooling", "cotton", "lightweight"])

    if any(w in cultural for w in ["islamic", "muslim", "modest"]):
        keywords.extend(["modest", "full-sleeve", "cotton", "traditional", "kurta"])
    if any(w in cultural for w in ["trek", "adventure", "outdoor", "hiking"]):
        keywords.extend(["trek", "outdoor", "waterproof", "durable", "backpack"])
    if any(w in cultural for w in ["wedding", "bridal", "festive", "occasion"]):
        keywords.extend(["silk", "traditional", "festive", "ethnic"])

    for need in needs:
        words = [w for w in need.lower().split() if len(w) > 3]
        keywords.extend(words[:3])

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
    avoid_categories: Optional[List[str]] = None,
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
        suggested_items_with_categories: Dict mapping item names to categories
        product_search_context: Dict with cultural_context, climate_note, product_needs
                                 from LLM detection for semantic scoring
        avoid_categories: Categories the user likely already owns (Memory Mining).
                          Products in these categories receive a -500 score penalty.

    Returns:
        List of product dicts, sorted by semantic trust score descending.
    """
    avoid_set = {c.lower().strip() for c in (avoid_categories or [])} if avoid_categories else set()

    products = _load_products()

    # ── Extract semantic context ───────────────────────────────────────────
    product_needs: List[str] = []
    cultural_keywords: List[str] = []
    if product_search_context:
        product_needs = product_search_context.get("product_needs", [])
        cultural_keywords = _extract_cultural_keywords(product_search_context)

    # ── 1. Filter by category (LLM-detected phases take priority) ─────────
    relevant = []
    if categories:
        relevant = [
            p for p in products
            if any(
                cat.lower() == p.get("category", "").lower()
                or p.get("category", "").lower().startswith(cat.lower())
                for cat in categories
            )
        ]

    # ── 1b. Apply event-aware blocklist (subcategory + name phrase) ──────────
    blocklist     = EVENT_SUBCATEGORY_BLOCKLIST.get(event_key, set())
    name_phrases  = EVENT_NAME_PHRASE_BLOCKLIST.get(event_key, set())
    if blocklist or name_phrases:
        def _is_blocked(p: Dict[str, Any]) -> bool:
            subcat      = (p.get("subcategory") or "").lower()
            category    = (p.get("category") or "").lower()
            name_lower  = (p.get("name") or "").lower()
            # Block by subcategory / category keyword
            for blocked in blocklist:
                if blocked in subcat or blocked in category:
                    return True
                # Legacy name check for longer terms in blocklist
                if len(blocked) > 5 and blocked.replace("_", " ") in name_lower:
                    return True
            # Block by name phrase (most reliable for mislabeled CSV rows)
            for phrase in name_phrases:
                if phrase in name_lower:
                    return True
            return False
        relevant = [p for p in relevant if not _is_blocked(p)]

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

    # ── 6. Score + category-balanced selection ────────────────────────────────
    # Sort all relevant products by score first
    def _score(product: Dict[str, Any]) -> float:
        score = _semantic_match_score(
            product,
            exact_items=exact_items,
            product_needs=product_needs,
            cultural_keywords=cultural_keywords,
        )
        if avoid_set:
            cat = product.get("category", "").lower()
            if any(avoided in cat or cat in avoided for avoided in avoid_set):
                score -= 500.0
        # Subcategory relevance boost for exact-item queries
        if exact_items:
            subcat = (product.get("subcategory") or "").lower()
            for item in exact_items:
                item_lower = item.lower()
                for term, subcat_map in SUBCATEGORY_RELEVANCE.items():
                    if term in item_lower:
                        boost = subcat_map.get(subcat, 0.0)
                        if boost > 0:
                            score += boost
                        elif subcat and subcat not in {"electronics", "gadgets"}:
                            score -= 200.0
                        break
        return score

    relevant.sort(key=_score, reverse=True)

    # ── Category-balanced selection ───────────────────────────────────────
    # Ensures EVERY phase category gets at least PER_CAT_MIN products in the
    # final list (before agents re-rank them). Without this, a high-scoring
    # category (e.g. shoes for first_job) monopolises the top-50 and other
    # phase categories (fashion_men, bags_luggage) get zero products.
    if categories and len(categories) > 1:
        PER_CAT_MIN = max(8, limit // max(len(categories), 1))
        cat_counts: Dict[str, int] = {}
        balanced: List[Dict[str, Any]] = []
        overflow: List[Dict[str, Any]] = []
        for p in relevant:
            p_cat = (p.get("category") or "").lower()
            matched_cat = next(
                (c for c in categories
                 if p_cat == c.lower() or p_cat.startswith(c.lower() + "_")),
                None,
            )
            if matched_cat and cat_counts.get(matched_cat, 0) < PER_CAT_MIN:
                balanced.append(p)
                cat_counts[matched_cat] = cat_counts.get(matched_cat, 0) + 1
            else:
                overflow.append(p)
        # Balanced pool first, then overflow for the remaining slots
        final_products = (balanced + overflow)[:limit]
    else:
        final_products = relevant[:limit]

    # ── 7. Product Gap Handling (Out of Stock cards) ──────────────────────
    items_to_check = []
    if exact_items:
        items_to_check.extend(
            [(item, categories[0] if categories else "generic") for item in exact_items]
        )
    if suggested_items_with_categories:
        items_to_check.extend(
            [(item, cat) for item, cat in suggested_items_with_categories.items()]
        )

    if items_to_check:
        for item, item_cat in reversed(items_to_check):
            item_words = set(w for w in item.lower().split() if len(w) > 3)
            if not item_words:
                item_words = set(item.lower().split())

            matched = False
            core_words = item_words - {
                "waterproof", "travel", "portable", "quick", "dry", "action",
                "smart", "electric", "digital", "mini",
            }
            if not core_words:
                core_words = item_words

            def _matches(p: Dict[str, Any]) -> bool:
                p_text = (
                    p.get("name", "") + " "
                    + " ".join(p.get("tags", [])) + " "
                    + p.get("description", "")
                ).lower()
                p_words = set(p_text.replace("-", " ").replace("_", " ").split())
                return bool(core_words.intersection(p_words))

            # Check if it's already in our filtered final_products
            for p in final_products:
                if _matches(p):
                    matched = True
                    break

            # TRICK: If not found in filtered list, check the ENTIRE database
            if not matched:
                for p in products:
                    if _matches(p):
                        # Force include this product into final_products
                        # It bypasses category/budget filters because it was explicitly requested!
                        forced_product = p.copy()
                        # Optional: re-assign its category so it appears in the right UI bucket,
                        # or let it keep its native category and appear in fallback rows.
                        final_products.insert(0, forced_product)
                        matched = True
                        break

            # If STILL not found in the entire database, then it's truly Out of Stock
            if not matched:
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


def select_top_picks(
    scored_products: List[Dict[str, Any]],
    top_picks_limit: int = 8,
    others_limit: int = 16,
) -> tuple:
    """
    Split a scored product list into two tiers for the two-row UI layout.

    Tier 1 — Top Picks (Row 1):
        The single highest-confidence_score product per subcategory.
        Guarantees that no two picks are from the same subcategory — the user
        sees one best bag, one best shoe, one best watch, etc.
        OOS (Out of Stock) gap cards are always included in top_picks so the
        user knows what's missing from the catalog.

    Tier 2 — Other Products (Row 2):
        Everything that didn't win its subcategory slot — sorted by score.
        These are valid alternatives and budget variants.

    The separation happens AFTER the 4 agents have run (confidence_score already
    reflects Kismat + Paisa + Samay + Soch votes), so "top picks" truly means
    "the product each agent collectively rated highest in its class".

    Args:
        scored_products: List of products already enriched with confidence_score
                         by the 4 agents in prism_service.py.
        top_picks_limit:  Max number of top picks to return (default 8).
        others_limit:     Max number of other products to return (default 16).

    Returns:
        (top_picks, other_products) — two separate sorted lists.
    """
    top_picks: List[Dict[str, Any]] = []
    other_products: List[Dict[str, Any]] = []
    seen_subcategories: set = set()

    # OOS cards get priority slots — they carry gap information, never deduplicated
    oos_cards = [p for p in scored_products if p.get("stock_status") == "out_of_stock"]
    in_stock = [p for p in scored_products if p.get("stock_status") != "out_of_stock"]

    # Sort in-stock by confidence_score descending (agents' collective verdict)
    in_stock_sorted = sorted(in_stock, key=lambda p: p.get("confidence_score", 0), reverse=True)

    for product in in_stock_sorted:
        # Build a dedup key: prefer subcategory, fall back to category
        subcat = product.get("subcategory") or product.get("category", "unknown")
        subcat_key = subcat.lower().strip()

        if subcat_key not in seen_subcategories:
            seen_subcategories.add(subcat_key)
            # Mark this product as a top pick for the frontend to style differently
            product["_is_top_pick"] = True
            top_picks.append(product)
        else:
            product["_is_top_pick"] = False
            other_products.append(product)

    # Prefix OOS gap cards into top_picks (users must see what PRISM couldn't find)
    for oos in oos_cards:
        oos["_is_top_pick"] = True
    top_picks = oos_cards + top_picks

    return top_picks[:top_picks_limit], other_products[:others_limit]
