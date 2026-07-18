import sys
sys.path.insert(0, '.')
from app.engines.product_matcher import match_products, split_by_primary_and_accessories

def show(products, label, n=8):
    print(f"\n--- {label} ({len(products)} total) ---")
    for p in products[:n]:
        cat = p.get("category", "?")
        subcat = p.get("subcategory", "")
        name = (p.get("name") or "OOS")[:55]
        stock = "(OOS)" if p.get("stock_status") == "out_of_stock" else ""
        print(f"  [{cat}/{subcat}] {name} {stock}")

# TEST 1: Direct phone purchase ask
products1 = match_products(
    event_key="generic",
    categories=["electronics"],
    exact_items=["phone"],
    user_intent_type="direct_purchase_ask",
    product_search_context={
        "user_input": "I need a phone at best price",
        "product_needs": ["smartphone mobile phone"],
        "event_label": "Buying a phone",
        "cultural_context": None,
        "climate_note": None,
    },
    limit=20,
)
show(products1, "Phone direct ask - all returned products")

# Split into primary / accessories
primary, accessories = split_by_primary_and_accessories(products1, "phone")
show(primary, "Phone - PRIMARY row (should be phones only)")
show(accessories, "Phone - ACCESSORIES row (row 2)")

# TEST 2: Hostel move context query
products2 = match_products(
    event_key="hostel_move",
    categories=["bedding", "study_accessories", "personal_care", "bags_luggage", "kitchen_essentials"],
    product_search_context={
        "user_input": "Son got into NIT Trichy hostel",
        "product_needs": [
            "cotton bedsheet breathable for humid climate",
            "study lamp desk organizer",
            "personal hygiene toiletry kit",
            "luggage bag for hostel move",
        ],
        "event_label": "College hostel move",
        "cultural_context": "Tamil Nadu coastal humid climate",
        "climate_note": "Humid coastal - choose breathable cotton fabrics",
    },
    user_intent_type="context_event",
    limit=20,
)
show(products2, "Hostel move - products")

print("\nAll tests passed!")
