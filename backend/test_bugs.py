import sys; sys.path.insert(0, ".")
from app.engines.product_matcher import (
    ACCESSORY_NAME_KEYWORDS, GLOBAL_ALWAYS_BLOCK_PHRASES,
    EVENT_SUBCATEGORY_BLOCKLIST, split_by_primary_and_accessories, _load_products
)

prods = _load_products()

# Bug 1: Junction box / extension board should be phone accessory
phone_acc = ACCESSORY_NAME_KEYWORDS.get("phone", set())
print("Bug1 - junction box in phone accessories:", "junction box" in phone_acc)
print("Bug1 - extension board in phone accessories:", "extension board" in phone_acc)
print("Bug1 - cleaning kit in phone accessories:", "cleaning kit" in phone_acc)
print("Bug1 - bluetooth speaker in phone accessories:", "bluetooth speaker" in phone_acc)

# Bug 4: Underwear/bikini global block
print("Bug4 - bikini in global block:", "bikini" in GLOBAL_ALWAYS_BLOCK_PHRASES)
print("Bug4 - underwear in global block:", "underwear" in GLOBAL_ALWAYS_BLOCK_PHRASES)

# Bug 3: automotive event has blocklist
auto_block = EVENT_SUBCATEGORY_BLOCKLIST.get("automotive", set())
print("Bug3 - automotive blocklist exists:", len(auto_block) > 0)

# Bug 2: Phone split - verify phone stays primary
phone_prods = [p for p in prods if any(k in (p.get("name","")).lower() for k in ["smartphone","redmi","galaxy","realme"])]
acc_prods = [p for p in prods if any(k in (p.get("name","")).lower() for k in ["extension board","junction box","cleaning kit","microphone","handheld mic"])]
print(f"Bug2 - phone products: {len(phone_prods)}, accessory products found: {len(acc_prods)}")
if acc_prods:
    pri, acc = split_by_primary_and_accessories(acc_prods + phone_prods[:5], "phone")
    acc_names = [p.get("name","")[:40] for p in acc]
    print(f"Bug2 - accessories correctly split: {len(acc)} items")
    for n in acc_names[:3]: print(f"  - {n}")
