import sys; sys.path.insert(0, ".")
from app.engines.product_matcher import (
    ACCESSORY_NAME_KEYWORDS, GLOBAL_ALWAYS_BLOCK_PHRASES,
    EVENT_SUBCATEGORY_BLOCKLIST, EVENT_NAME_PHRASE_BLOCKLIST,
    split_by_primary_and_accessories, _load_products, match_products
)
from app.engines.life_event_engine import LifeEventEngine

prods = _load_products()
print(f"Catalog loaded: {len(prods)} products\n")

# -- Bug 1: Junction box stays as phone accessory ------------------------------
phone_acc = ACCESSORY_NAME_KEYWORDS.get("phone", set())
bugs = {
    "Bug1 - junction box is phone accessory": "junction box" in phone_acc,
    "Bug1 - extension board is phone accessory": "extension board" in phone_acc,
    "Bug1 - cleaning kit is phone accessory": "cleaning kit" in phone_acc,
    "Bug1 - bluetooth speaker is phone accessory": "bluetooth speaker" in phone_acc,
    "Bug1 - microphone is phone accessory": "microphone" in phone_acc,
}

# -- Bug 4: Underwear/bikini global block --------------------------------------
bugs["Bug4 - bikini in global block"] = "bikini" in GLOBAL_ALWAYS_BLOCK_PHRASES
bugs["Bug4 - underwear in global block"] = "underwear" in GLOBAL_ALWAYS_BLOCK_PHRASES
bugs["Bug4 - lingerie in global block"] = "lingerie" in GLOBAL_ALWAYS_BLOCK_PHRASES

# -- Bug 3: Automotive blocklist -----------------------------------------------
auto_block = EVENT_SUBCATEGORY_BLOCKLIST.get("automotive", set())
bugs["Bug3 - automotive has blocklist"] = len(auto_block) > 0

# -- Bug 2: Phone split - extension boards go to accessories ------------------
test_prods = [
    {"id": "P1", "name": "Redmi Note 12 (6GB RAM, 128GB Storage)", "category": "electronics", "subcategory": "smartphones", "price": 12999, "stock_status": "in_stock"},
    {"id": "P2", "name": "4 Socket Extension Board with Surge Protection", "category": "electronics", "subcategory": "accessories", "price": 499, "stock_status": "in_stock"},
    {"id": "P3", "name": "MAONO Handheld Dynamic Microphone", "category": "electronics", "subcategory": "instruments", "price": 999, "stock_status": "in_stock"},
    {"id": "P4", "name": "Zebronics Bluetooth Portable Speaker", "category": "electronics", "subcategory": "speakers", "price": 799, "stock_status": "in_stock"},
    {"id": "P5", "name": "Samsung Galaxy M33 5G (6GB, 128GB)", "category": "electronics", "subcategory": "smartphones", "price": 14999, "stock_status": "in_stock"},
]
pri, acc = split_by_primary_and_accessories(test_prods, "phone")
bugs["Bug2 - Redmi stays primary"] = any("Redmi" in p["name"] for p in pri)
bugs["Bug2 - Extension board goes accessory"] = any("Extension Board" in p["name"] for p in acc)
bugs["Bug2 - Microphone goes accessory"] = any("Microphone" in p["name"] for p in acc)
bugs["Bug2 - Speaker goes accessory"] = any("Speaker" in p["name"] for p in acc)

# -- Bug 5&6: match_products for car event returns automotive ------------------
car_products = match_products(
    event_key="generic",
    limit=10,
    categories=["automotive"],
    exact_items=["car seat cover"],
    product_search_context={"user_input": "I bought a new car", "product_needs": ["car seat cover", "dash cam"]},
)
bugs["Bug3 - car query returns products"] = len(car_products) > 0
if car_products:
    print("Car query products:")
    for p in car_products[:3]:
        print(f"  - {p.get('name','')[:50]} [{p.get('category')}]")

# -- Print all results ---------------------------------------------------------
print("\n=== Bug Fix Validation ===")
all_pass = True
for name, result in bugs.items():
    status = "? PASS" if result else "? FAIL"
    if not result: all_pass = False
    print(f"  {status} | {name}")
print(f"\nOverall: {'ALL PASS' if all_pass else 'SOME FAILED'}")
