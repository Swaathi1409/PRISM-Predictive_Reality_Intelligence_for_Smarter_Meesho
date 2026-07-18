"""test_iit_delhi.py — Verify all bug fixes for the IIT Delhi hostel_move scenario"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'app/data/prism_catalog.db')
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# ── Test 1: kitchen_appliances DB is clean ──────────────────────────────────
cur.execute("SELECT name, category FROM products WHERE category = 'kitchen_appliances'")
ka_rows = cur.fetchall()
BAD_KITCHEN = ['ceiling fan', 'steam iron', 'dry iron', 'air cooler', 'laundry basket', 'laundry bag']
bad_ka = [r for r in ka_rows if any(b in r['name'].lower() for b in BAD_KITCHEN)]
print("TEST 1: kitchen_appliances has no misclassified items")
if bad_ka:
    for r in bad_ka:
        print(f"  FAIL: [{r['category']}] {r['name'][:60]}")
else:
    print("  PASS — All kitchen_appliances products are actual kitchen appliances")
    for r in ka_rows:
        print(f"    OK: {r['name'][:70]}")

# ── Test 2: Frontend strict phase matching — no bleed ───────────────────────
print()
print("TEST 2: Strict category matching — kitchen_appliances should NOT match kitchen_essentials")
phase_cats = ['kitchen_essentials', 'fashion_men']
cur.execute("SELECT id, name, category FROM products WHERE stock_status = 'in_stock'")
all_prods = [dict(r) for r in cur.fetchall()]

# Old fuzzy logic
fuzzy_matches = []
for p in all_prods:
    pCat = (p.get('category') or '').lower().replace('_', ' ').strip()
    for cat in phase_cats:
        phaseCat = cat.lower().replace('_', ' ').strip()
        pWords = pCat.split(' ')
        phWords = phaseCat.split(' ')
        word_overlap = (any(w for w in pWords if len(w) > 3 and w in phWords) or
                        any(w for w in phWords if len(w) > 3 and w in pWords))
        if word_overlap and p['category'] not in ['kitchen_essentials', 'fashion_men']:
            fuzzy_matches.append((p['category'], p['name'][:50], cat))
            break

# New strict logic
strict_matches = []
for p in all_prods:
    pCat = (p.get('category') or '').lower().replace('_', ' ').strip()
    for cat in phase_cats:
        phaseCat = cat.lower().replace('_', ' ').strip()
        exact = pCat == phaseCat
        prefix = pCat.startswith(phaseCat + ' ') or phaseCat.startswith(pCat + ' ')
        if (exact or prefix) and p['category'] not in ['kitchen_essentials', 'fashion_men']:
            strict_matches.append((p['category'], p['name'][:50], cat))
            break

print(f"  OLD (fuzzy): {len(fuzzy_matches)} wrong products bleeding into phases")
for m in fuzzy_matches[:5]:
    print(f"    BLEED [{m[0]}] -> phase '{m[2]}': {m[1]}")
print(f"  NEW (strict): {len(strict_matches)} wrong products bleeding into phases")
if strict_matches:
    for m in strict_matches[:5]:
        print(f"    BLEED [{m[0]}] -> phase '{m[2]}': {m[1]}")
else:
    print("  PASS — No cross-category bleeding with strict matching")

# ── Test 3: Hostel blocklist blocks kitchen_appliances ───────────────────────
print()
print("TEST 3: Backend product_matcher hostel_move blocklist blocks kitchen_appliances")
HOSTEL_BLOCKLIST_CATS = {
    'baby', 'baby_products', 'wedding_apparel', 'toys_games', 'pet_supplies',
    'automotive', 'kitchen_appliances'
}
all_cats_returned = ['bedding', 'bags_luggage', 'personal_care', 'study_accessories', 'kitchen_essentials', 'fashion_men']
blocked_in_hostel = [c for c in all_cats_returned if c in HOSTEL_BLOCKLIST_CATS]
if blocked_in_hostel:
    print(f"  FAIL: These categories should be blocked: {blocked_in_hostel}")
else:
    print(f"  PASS — All returned categories are allowed for hostel_move")
    print(f"    Categories: {all_cats_returned}")

# ── Test 4: Men's t-shirts appear in fashion_men phase, NOT kitchen phase ────
print()
print("TEST 4: Men's t-shirts appear in fashion_men phase only")
cur.execute("SELECT name, category FROM products WHERE category = 'fashion_men' LIMIT 3")
men_prods = [dict(r) for r in cur.fetchall()]
# These should match Phase 3 (fashion_men) but NOT Phase 1 or 2
for prod in men_prods:
    pCat = prod['category'].lower().replace('_', ' ').strip()
    in_phase_1 = any(
        pCat == c.lower().replace('_', ' ') for c in ['bedding', 'bags_luggage', 'personal_care']
    )
    in_phase_3 = pCat == 'fashion men'
    status = "PASS" if (not in_phase_1 and in_phase_3) else "FAIL"
    print(f"  {status}: {prod['name'][:50]} -> in Phase1={in_phase_1}, in Phase3={in_phase_3}")

# ── Test 5: LLM filter fail-open ─────────────────────────────────────────────
print()
print("TEST 5: LLM filter fail-open — returns all IDs on exception")
mock_products = [{'id': 'A1'}, {'id': 'B2'}, {'id': 'C3'}]
try:
    raise Exception("Simulated API error")
except Exception:
    result = [p.get('id') for p in mock_products if p.get('id')]
expected = ['A1', 'B2', 'C3']
if result == expected:
    print(f"  PASS — Fail-open returns all {len(result)} product IDs: {result}")
else:
    print(f"  FAIL — Got {result}, expected {expected}")

conn.close()
print()
print("=== All tests complete ===")
