"""
product_matcher.py — Filters and ranks products from SQLite catalog for a given life event.

WHY THIS MODULE EXISTS:
Product selection must be driven by the detected life event, Bharat context,
AND the user's specific cultural/climate needs — not just hardcoded event tags.

RETRIEVAL PIPELINE (v2 — RAG-first):
  Stage 1: Embedding-based semantic retrieval (FAISS)
           - For specific-item asks: embed the item name → cosine retrieval
           - For context queries: embed each product_need phrase → batch retrieval
           - Returns top-K candidates ranked by semantic similarity
  Stage 2: Category post-filter (guardrail only)
           - Removes products from completely wrong domains
           - Does NOT restrict within the right domain
  Stage 3: Institution constraints (wattage, prohibited)
  Stage 4: Budget filter
  Stage 5: Hybrid scoring
           - 60% embedding cosine + 40% trust/cultural semantic score
  Stage 6: Category-balanced selection (ensures phase diversity)
  Stage 7: OOS gap handling

TWO-TIER OUTPUT:
  top_picks    — best 1 product per subcategory (selected by composite 4-agent score).
  other_products — remaining scored products for the "More to Explore" row.

Fallback: if FAISS/sentence-transformers not available, falls back to v1 category matching.

Libraries: json (stdlib), math (stdlib), sqlite3 (stdlib), app.config (internal),
           app.engines.embedding_index (internal).
"""

import json
import math
import os
import sqlite3
from typing import List, Dict, Any, Optional, Tuple

from app.engines.embedding_index import get_index, is_rag_available

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
    "generic": {
        "baby", "baby_products", "feeding_bottle", "diaper", "nappy",
        "wedding_apparel", "bridal", "exam_supplies", "toys_games",
    },
}


# ── Name-phrase blocklist (catches products by actual name keywords) ───────────
EVENT_NAME_PHRASE_BLOCKLIST: Dict[str, set] = {
    "hostel_move": {
        "baby", "infant", "newborn", "new born", "neonatal", "nursery",
        "steriliz", "feeding bottle", "nipple", "pacifier", "nappy",
        "diaper", "pram", "stroller", "teether", "swaddle", "baby bib",
        "changing mat", "baby pillow", "baby blanket",
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
    "generic": {
        "baby", "infant", "diaper",
        "harpic", "lizol", "domex", "toilet cleaner", "floor cleaner",
        "washing machine cleaner", "descaling",
        "comprehension skills", "short passages",
        "shirt stays", "shirt garters",
    },
}


# ── Primary item subcategories for the specific-ask two-tier display ──────────
# Used as a fallback when embeddings are unavailable.
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

# ── Primary name-keyword patterns (definitive classification) ────────────────
# Products whose names contain ANY of these keywords are DEFINITELY the primary item.
# This is the highest-confidence signal — applied before embedding comparison.
PRIMARY_NAME_KEYWORDS: Dict[str, set] = {
    # Phone: use storage/RAM patterns & model numbers that ONLY appear in phone names
    "phone":      {"smartphone", "android phone", "mobile phone",
                   "128gb storage", "64gb storage", "256gb storage", "512gb storage",
                   "6gb, 128gb", "8gb, 128gb", "6gb, 64gb", "4gb, 64gb", "6gb ram,",
                   "redmi note", "redmi a", "galaxy m", "galaxy a", "galaxy s",
                   "realme c", "realme narzo", "realme gt",
                   "poco x", "poco m", "poco f",
                   "vivo y", "vivo v", "oppo a", "oppo f", "oppo reno",
                   "nord ce", "nord lite", "nord 2",
                   "iphone 1", "iphone se", "iphone pro"},
    "mobile":     {"smartphone", "android phone", "mobile phone",
                   "gb, 128gb", "gb, 64gb", "gb ram,",
                   "redmi note", "galaxy m", "realme c", "poco x"},
    "smartphone": {"smartphone", "android phone",
                   "gb ram", "redmi", "realme c", "poco"},
    "laptop":     {"laptop", "macbook", "vivobook", "ideapad", "inspiron", "pavilion",
                   "thinkpad", "elitebook", "chromebook", "notebook"},
    "earphone":   {"earphone", "earbuds", "tws ", "neckband", "in ear headphone",
                   "wireless in ear", "wired earphone", "in-ear headphone"},
    "earphones":  {"earphone", "earbuds", "tws ", "neckband", "in ear headphone",
                   "wireless in ear"},
    "headphone":  {"headphone", "over-ear headphone", "on-ear headphone",
                   "over ear headphone"},
    "headphones": {"headphone", "over-ear headphone", "on-ear headphone"},
    "speaker":    {"bluetooth speaker", "portable speaker", "wireless speaker",
                   "soundbar", "home theatre"},
    "watch":      {"smartwatch", "smart watch", "analog watch", "digital watch",
                   "wrist watch", "chronograph", "fitness watch"},
    "smartwatch": {"smartwatch", "smart watch", "fitness tracker"},
    "tablet":     {"tablet", "ipad", "galaxy tab", "tab s", "tab a"},
    "camera":     {"dslr camera", "mirrorless camera", "digital camera",
                   "action camera", "webcam", "point and shoot"},
    "tv":         {"smart tv", "led tv", "oled tv", "4k tv", "android tv",
                   "qled", "qhd tv", "full hd tv"},
    "television": {"smart tv", "led tv", "oled tv", "4k tv", "android tv",
                   "qled", "full hd tv"},
    "refrigerator": {"refrigerator", "frost free", "double door fridge",
                     "single door fridge", "inverter compressor"},
    "fridge":     {"refrigerator", "frost free", "double door"},
    "washing machine": {"washing machine", "front load", "top load", "fully automatic"},
    "microwave":  {"microwave oven", "convection microwave", "solo microwave"},
    "mixer":      {"mixer grinder", "juicer mixer"},
    "ac":         {"split ac", "window ac", "inverter ac", "air conditioner"},
    "air conditioner": {"split ac", "window ac", "inverter ac", "air conditioner"},
}

# ── Accessory name keywords (definitive accessory classification) ──────────────
ACCESSORY_NAME_KEYWORDS: Dict[str, set] = {
    "phone":      {"charger", "charging cable", "data cable", "usb cable",
                   "fast charging cable", "fast charge", "braided cable",
                   "phone cover", "back cover", "phone case", "screen protector",
                   "tempered glass", "phone holder", "phone stand", "selfie stick",
                   "tripod", "gorilla tripod", "phone grip", "pop socket",
                   "microsd", "micro sd", "memory card", "sandisk", "samsung evo"},
    "laptop":     {"laptop bag", "laptop sleeve", "cooling pad", "laptop stand",
                   "laptop mouse", "laptop keyboard", "usb hub", "laptop charger",
                   "screen cleaner", "laptop skin"},
    "earphone":   {"earphone case", "ear tip", "ear cushion"},
    "headphone":  {"headphone stand", "headphone case"},
    "speaker":    {"speaker stand", "aux cable", "speaker wire"},
    "watch":      {"watch strap", "watch band", "watch charger", "watch case"},
    "camera":     {"tripod", "camera bag", "lens filter", "memory card", "camera strap",
                   "camera stand", "gorilla pod", "monopod", "backdrop"},
    "tv":         {"wall mount", "tv stand", "hdmi cable", "remote cover"},
    "refrigerator": {"fridge organizer", "ice tray", "water bottle for fridge"},
}


def _is_primary_by_name(product: Dict[str, Any], keyword: str) -> Optional[bool]:
    """
    Returns True if product name strongly indicates it IS the primary item.
    Returns False if product name strongly indicates it IS an accessory.
    Returns None if name is ambiguous (let embedding decide).
    """
    name_lower = (product.get("name") or "").lower()
    subcat = (product.get("subcategory") or "").lower()

    # Check accessory name patterns first (accessories are often named with primary keywords too)
    acc_patterns = ACCESSORY_NAME_KEYWORDS.get(keyword, set())
    if any(pat in name_lower for pat in acc_patterns):
        return False  # Definitely an accessory

    # Check primary name patterns
    pri_patterns = PRIMARY_NAME_KEYWORDS.get(keyword, set())
    if any(pat in name_lower for pat in pri_patterns):
        return True  # Definitely the primary item

    # Check subcategory against known primary subcats
    primary_subcats = PRIMARY_SUBCATEGORIES.get(keyword, set())
    if primary_subcats and subcat in primary_subcats:
        return True

    return None  # Ambiguous — let embedding decide


# ── Accessory query texts for embedding-based split ───────────────────────────
# When user asks for primary item X, we embed these descriptions to identify accessories.
ACCESSORY_QUERIES: Dict[str, str] = {
    "phone":        "phone charger cable cover case screen protector earphone",
    "mobile":       "mobile charger cable cover case screen protector",
    "smartphone":   "smartphone charger cable cover case screen protector earphone",
    "laptop":       "laptop bag mouse keyboard cooling pad screen cleaner usb hub",
    "earphone":     "earphone case cable audio adapter",
    "earphones":    "earphone case cable audio adapter",
    "headphone":    "headphone stand cable audio adapter",
    "headphones":   "headphone stand cable audio adapter",
    "charger":      "charging cable adapter power strip",
    "powerbank":    "power bank cable adapter",
    "speaker":      "speaker cable bluetooth adapter aux",
    "watch":        "watch strap band charger",
    "smartwatch":   "smartwatch strap band charger",
    "tablet":       "tablet cover stylus keyboard stand",
    "camera":       "camera bag tripod memory card lens filter",
    "tv":           "tv remote cable mount wall bracket soundbar",
    "television":   "tv remote cable mount wall bracket soundbar",
    "refrigerator": "fridge organizer shelf ice tray food containers",
    "fridge":       "fridge organizer shelf ice tray food containers",
    "washing machine": "laundry bag detergent fabric softener lint roller",
    "microwave":    "microwave safe container oven mitt baking tray",
    "mixer":        "mixer jar attachment",
    "blender":      "blender jar bottle",
    "ac":           "ac cover air filter remote",
    "air conditioner": "ac cover filter remote",
}


def split_by_primary_and_accessories(
    products: List[Dict[str, Any]],
    primary_keyword: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Split a product list into (primary_products, accessory_products).

    Strategy (3-tier, most reliable first):
    1. Name-keyword check (definitive) — catches brands, specific product names
    2. Embedding cosine comparison (for ambiguous products)
    3. Subcategory fallback (when embeddings unavailable)
    """
    keyword = primary_keyword.lower().strip()
    oos_items = [p for p in products if p.get("stock_status") == "out_of_stock"]
    in_stock = [p for p in products if p.get("stock_status") != "out_of_stock"]

    primary: List[Dict[Any, Any]] = []
    accessories: List[Dict[Any, Any]] = []
    ambiguous: List[Dict[Any, Any]] = []  # Products needing embedding decision

    # ── Tier 1: Name-keyword check (most reliable) ─────────────────────────
    for p in in_stock:
        verdict = _is_primary_by_name(p, keyword)
        if verdict is True:
            primary.append(p)
        elif verdict is False:
            accessories.append(p)
        else:
            ambiguous.append(p)  # Let embedding decide

    # ── Tier 2: Embedding for ambiguous products ───────────────────────────
    if ambiguous:
        index = get_index()
        if index.is_available:
            primary_query = keyword
            accessory_query = ACCESSORY_QUERIES.get(keyword, f"{keyword} accessory case cable charger")

            primary_emb = index.get_embedding(primary_query)
            accessory_emb = index.get_embedding(accessory_query)

            if primary_emb is not None and accessory_emb is not None:
                from app.engines.embedding_index import _product_to_text
                for p in ambiguous:
                    prod_text = _product_to_text(p)
                    prod_emb = index.get_embedding(prod_text)
                    if prod_emb is None:
                        accessories.append(p)  # Unknown → treat as accessory
                        continue

                    sim_primary = index.cosine_similarity(prod_emb, primary_emb)
                    sim_accessory = index.cosine_similarity(prod_emb, accessory_emb)

                    # Require primary similarity to be meaningfully higher
                    # (bias 0.03 favors primary to avoid under-showing the item)
                    if sim_primary >= sim_accessory - 0.03:
                        primary.append(p)
                    else:
                        accessories.append(p)
                return oos_items + primary, accessories

        # Tier 3: Subcategory fallback for ambiguous products
        primary_subcats = PRIMARY_SUBCATEGORIES.get(keyword, set())
        for p in ambiguous:
            _fallback_split(p, keyword, primary, accessories, primary_subcats)

    return oos_items + primary, accessories


def _fallback_split(
    p: Dict[str, Any],
    keyword: str,
    primary: List,
    accessories: List,
    primary_subcats: Optional[set] = None,
):
    """Subcategory/name-based split fallback for when embeddings aren't available."""
    if primary_subcats is None:
        primary_subcats = PRIMARY_SUBCATEGORIES.get(keyword, set())
    subcat = (p.get("subcategory") or "").lower()
    name_lower = (p.get("name") or "").lower()

    if primary_subcats and subcat in primary_subcats:
        primary.append(p)
    elif keyword in name_lower and (not primary_subcats or subcat in primary_subcats):
        primary.append(p)
    else:
        accessories.append(p)


def _row_to_product(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a SQLite Row to the product dict format used by the rest of PRISM."""
    p = dict(row)
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
    """Loads product catalog once into module-level cache."""
    global _products_cache
    if _products_cache is not None:
        return _products_cache

    if os.path.exists(_DB_PATH):
        _products_cache = _load_products_from_sqlite()
    else:
        _products_cache = _load_products_from_json()

    return _products_cache


def invalidate_cache():
    """Call this after rebuilding the SQLite DB to force a reload."""
    global _products_cache
    _products_cache = None
    from app.engines.embedding_index import PRISMEmbeddingIndex
    PRISMEmbeddingIndex.invalidate()


# ── RAG query builder ─────────────────────────────────────────────────────────

def _build_rag_query(
    user_input: str,
    product_needs: Optional[List[str]] = None,
    exact_items: Optional[List[str]] = None,
    event_label: Optional[str] = None,
    cultural_context: Optional[str] = None,
) -> str:
    """
    Builds a rich composite query string for the embedding search.
    For specific items: uses the item name directly.
    For context queries: combines product_needs + event context.
    """
    parts = []

    # Specific items are the strongest signal
    if exact_items:
        parts.extend(exact_items)

    # Product needs from LLM are highly specific
    if product_needs:
        parts.extend(product_needs[:5])

    # Event label and cultural context add general context
    if event_label and event_label.lower() not in ("shopping assistance", "generic"):
        parts.append(event_label)

    if cultural_context:
        # Keep only first 100 chars to avoid dilution
        parts.append(cultural_context[:100])

    # Fallback: raw user input
    if not parts and user_input:
        parts.append(user_input)

    return " ".join(filter(None, parts))


def _build_context_rag_queries(
    product_needs: Optional[List[str]] = None,
    event_label: Optional[str] = None,
    user_input: Optional[str] = None,
    categories: Optional[List[str]] = None,
) -> List[str]:
    """
    For context-based queries (hostel move, wedding, etc.), builds multiple
    focused query strings — one per product_need phrase — for batch embedding search.
    This lets us find products that match each specific need semantically.
    """
    queries = []

    if product_needs:
        for need in product_needs[:6]:
            queries.append(need)

    if event_label and event_label.lower() not in ("shopping assistance", "generic"):
        queries.append(event_label)

    # Category-level queries as lightweight fallback queries
    if categories:
        for cat in categories[:4]:
            queries.append(cat.replace("_", " "))

    if not queries and user_input:
        queries.append(user_input)

    return queries


# ── Semantic trust score (non-embedding component) ───────────────────────────

def _semantic_match_score(
    product: Dict[str, Any],
    exact_items: Optional[List[str]] = None,
    product_needs: Optional[List[str]] = None,
    cultural_keywords: Optional[List[str]] = None,
) -> float:
    """
    Non-embedding trust score:
    - Base: seller_rating × log(reviews) - return_rate_penalty
    - Exact item boost
    - Product needs word-overlap boost
    - Cultural/climate keyword boost
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

    if product_needs:
        for need in product_needs:
            need_words = set(
                w for w in need.lower().replace("-", " ").split()
                if len(w) > 2 and w not in {"and", "the", "with", "for", "a", "an", "of", "to"}
            )
            overlap = need_words.intersection(product_words)
            if overlap:
                base_score += 200.0 * (len(overlap) / max(len(need_words), 1))

    if cultural_keywords:
        for kw in cultural_keywords:
            kw_lower = kw.lower()
            if kw_lower in product_text:
                base_score += 150.0

    return base_score


def _extract_cultural_keywords(product_search_context: Optional[Dict]) -> List[str]:
    """Extracts climate/cultural keywords from the LLM context for boost scoring."""
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


# ── Main matching function ────────────────────────────────────────────────────

def match_products(
    event_key: str,
    institution_data: Optional[Dict] = None,
    budget: Optional[int] = None,
    pincode: str = "600001",
    limit: int = 50,
    categories: Optional[List[str]] = None,
    exact_items: Optional[List[str]] = None,
    suggested_items_with_categories: Optional[Dict[str, str]] = None,
    product_search_context: Optional[Dict] = None,
    avoid_categories: Optional[List[str]] = None,
    user_intent_type: Optional[str] = None,  # NEW: from LLM detection
) -> List[Dict[str, Any]]:
    """
    Returns up to `limit` products relevant to the given life event.

    RAG-first pipeline:
    1. Embedding semantic search → primary candidates
    2. Category post-filter guardrail (wrong domain removal)
    3. Institution constraints
    4. Budget filter
    5. Hybrid scoring (60% embedding + 40% trust/cultural)
    6. Category-balanced selection
    7. OOS gap cards
    """
    avoid_set = {c.lower().strip() for c in (avoid_categories or [])} if avoid_categories else set()
    products = _load_products()

    # ── Extract semantic context ───────────────────────────────────────────
    product_needs: List[str] = []
    cultural_keywords: List[str] = []
    if product_search_context:
        product_needs = product_search_context.get("product_needs", [])
        cultural_keywords = _extract_cultural_keywords(product_search_context)

    event_label = product_search_context.get("event_label", "") if product_search_context else ""

    # ── Stage 1: Embedding-based retrieval ────────────────────────────────
    # Build a dict of {product_id: embedding_cosine_score}
    embedding_scores: Dict[str, float] = {}
    rag_used = False

    index = get_index()
    if index.is_available:
        # Ensure index is built (lazy load from disk or build fresh)
        def _loader():
            return _load_products()

        is_specific = bool(exact_items) or (user_intent_type == "direct_purchase_ask")

        if is_specific and exact_items:
            # Specific-item ask: search for BOTH the primary item AND its accessories
            # so the full pool has both types with differentiated scores.
            primary_rag_query = " ".join(exact_items[:3])
            acc_query = ACCESSORY_QUERIES.get(exact_items[0].lower().strip(),
                                              f"{primary_rag_query} accessory case cable")

            # Primary search: high-k to capture all real products
            primary_results = index.search(
                primary_rag_query, k=min(80, len(products)), products_loader=_loader
            )
            # Accessory search: separate query to get accessories in pool too
            acc_results = index.search(
                acc_query, k=min(40, len(products)), products_loader=_loader
            )

            # Merge: primary scores take precedence; accessory scores fill gaps
            embedding_scores = {pid: score for pid, score in primary_results}
            for pid, score in acc_results:
                if pid not in embedding_scores:
                    embedding_scores[pid] = score * 0.9  # slight penalty for acc-only hits

            rag_used = bool(embedding_scores)
        else:
            # Context query: batch search across product_needs phrases
            context_queries = _build_context_rag_queries(
                product_needs=product_needs,
                event_label=event_label,
                user_input=product_search_context.get("user_input", "") if product_search_context else "",
                categories=categories,
            )
            if context_queries:
                embedding_scores = index.search_batch(
                    context_queries,
                    k_per_query=min(60, len(products)),
                    products_loader=_loader,
                )
                rag_used = bool(embedding_scores)

    # ── Stage 2: Category post-filter guardrail ───────────────────────────
    # Primary filter: if RAG gave us results, use them as the candidate pool
    # If not, fall back to category-string filter (v1 behavior)
    if rag_used and embedding_scores:
        # Products ranked by embedding score — keep those in valid categories
        scored_by_embedding = [
            p for p in products
            if p.get("id") in embedding_scores
        ]

        # If we have categories, apply them as a GUARDRAIL (not strict gate)
        # Only filter out products from TOTALLY wrong categories
        if categories:
            valid_cats = {c.lower() for c in categories}
            # Keep product if its category is in valid_cats OR it scored very high
            # High-scoring products from adjacent categories are often still relevant
            HIGH_SCORE_THRESHOLD = 0.55  # cosine sim — keep regardless of category
            relevant = [
                p for p in scored_by_embedding
                if (
                    any(
                        p.get("category", "").lower() == cat or
                        p.get("category", "").lower().startswith(cat + "_")
                        for cat in valid_cats
                    )
                    or embedding_scores.get(p.get("id"), 0) >= HIGH_SCORE_THRESHOLD
                )
            ]
            if not relevant:
                relevant = scored_by_embedding  # All are relevant by embedding
        else:
            relevant = scored_by_embedding

        # If RAG pool is too small (< 10 products), augment with category fallback
        if len(relevant) < 10 and categories:
            cat_pool = [
                p for p in products
                if any(
                    cat.lower() == p.get("category", "").lower() or
                    p.get("category", "").lower().startswith(cat.lower() + "_")
                    for cat in categories
                ) and p.get("id") not in embedding_scores
            ]
            relevant.extend(cat_pool[:30])

    else:
        # ── V1 category-string fallback (RAG unavailable) ─────────────────
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
        if not relevant:
            relevant = [p for p in products if event_key in p.get("event_tags", [])]
        if not relevant:
            relevant = list(products)

    # ── Apply event-aware blocklist (subcategory + name phrase) ──────────
    blocklist = EVENT_SUBCATEGORY_BLOCKLIST.get(event_key, set())
    name_phrases = EVENT_NAME_PHRASE_BLOCKLIST.get(event_key, set())
    if blocklist or name_phrases:
        def _is_blocked(p: Dict[str, Any]) -> bool:
            subcat = (p.get("subcategory") or "").lower()
            category = (p.get("category") or "").lower()
            name_lower = (p.get("name") or "").lower()
            for blocked in blocklist:
                if blocked in subcat or blocked in category:
                    return True
                if len(blocked) > 5 and blocked.replace("_", " ") in name_lower:
                    return True
            for phrase in name_phrases:
                if phrase in name_lower:
                    return True
            return False
        relevant = [p for p in relevant if not _is_blocked(p)]

    # ── Stage 3: Institution constraints ─────────────────────────────────
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

    # ── Stage 4: Budget filter ────────────────────────────────────────────
    if budget and budget > 0:
        relevant = [p for p in relevant if p.get("price", 0) <= budget]

    # ── Stage 5: Hybrid scoring ───────────────────────────────────────────
    # Combine embedding cosine similarity (60%) with trust/cultural score (40%)
    EMBEDDING_WEIGHT = 0.60
    TRUST_WEIGHT = 0.40

    # Find max trust score for normalisation
    trust_scores_raw = {
        p.get("id"): _semantic_match_score(
            p,
            exact_items=exact_items,
            product_needs=product_needs,
            cultural_keywords=cultural_keywords,
        )
        for p in relevant
    }
    max_trust = max(trust_scores_raw.values(), default=1.0)
    if max_trust <= 0:
        max_trust = 1.0

    def _hybrid_score(product: Dict[str, Any]) -> float:
        pid = product.get("id")
        emb_score = embedding_scores.get(pid, 0.0) if rag_used else 0.0
        trust = trust_scores_raw.get(pid, 0.0)
        trust_norm = trust / max_trust  # normalise to [0, 1]

        if rag_used:
            score = EMBEDDING_WEIGHT * emb_score + TRUST_WEIGHT * trust_norm
        else:
            # RAG unavailable — trust score is the only signal (scaled)
            score = trust

        # Avoid-category penalty
        if avoid_set:
            cat = product.get("category", "").lower()
            if any(avoided in cat or cat in avoided for avoided in avoid_set):
                score -= 0.3 if rag_used else 500.0

        return score

    relevant.sort(key=_hybrid_score, reverse=True)

    # ── Stage 6: Category-balanced selection ──────────────────────────────
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
        final_products = (balanced + overflow)[:limit]
    else:
        final_products = relevant[:limit]

    # ── Stage 7: OOS gap cards ─────────────────────────────────────────────
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
        final_product_ids = {p.get("id") for p in final_products}
        for item, item_cat in reversed(items_to_check):
            item_words = set(w for w in item.lower().split() if len(w) > 3)
            if not item_words:
                item_words = set(item.lower().split())

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

            matched = any(_matches(p) for p in final_products)

            if not matched:
                # Check entire DB
                for p in products:
                    if _matches(p):
                        forced = p.copy()
                        final_products.insert(0, forced)
                        matched = True
                        break

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
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Split a scored product list into two tiers for the two-row UI layout.

    Tier 1 — Top Picks (Row 1):
        The single highest-confidence_score product per subcategory.
    Tier 2 — Other Products (Row 2):
        Everything else — sorted by score.
    """
    top_picks: List[Dict[str, Any]] = []
    other_products: List[Dict[str, Any]] = []
    seen_subcategories: set = set()

    oos_cards = [p for p in scored_products if p.get("stock_status") == "out_of_stock"]
    in_stock = [p for p in scored_products if p.get("stock_status") != "out_of_stock"]

    in_stock_sorted = sorted(in_stock, key=lambda p: p.get("confidence_score", 0), reverse=True)

    for product in in_stock_sorted:
        subcat = product.get("subcategory") or product.get("category", "unknown")
        subcat_key = subcat.lower().strip()

        if subcat_key not in seen_subcategories:
            seen_subcategories.add(subcat_key)
            product["_is_top_pick"] = True
            top_picks.append(product)
        else:
            product["_is_top_pick"] = False
            other_products.append(product)

    for oos in oos_cards:
        oos["_is_top_pick"] = True
    top_picks = oos_cards + top_picks

    return top_picks[:top_picks_limit], other_products[:others_limit]
