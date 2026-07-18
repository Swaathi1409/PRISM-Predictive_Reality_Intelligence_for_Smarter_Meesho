"""fix_db_categories.py -- Fix miscategorized products in prism_catalog.db"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'app/data/prism_catalog.db')

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 1. Move ceiling fans to appliances
cur.execute(
    "UPDATE products SET category = 'appliances', subcategory = 'fans' "
    "WHERE category = 'kitchen_appliances' AND ("
    "  LOWER(name) LIKE '%ceiling fan%' OR LOWER(name) LIKE '%table fan%'"
    ")"
)
print(f"Ceiling fans moved to appliances: {cur.rowcount}")

# 2. Move irons to appliances
cur.execute(
    "UPDATE products SET category = 'appliances', subcategory = 'irons' "
    "WHERE category = 'kitchen_appliances' AND ("
    "  LOWER(name) LIKE '% iron %' OR LOWER(name) LIKE '%steam iron%' "
    "  OR LOWER(name) LIKE '%dry iron%' OR LOWER(name) LIKE '%iron with%'"
    ")"
)
print(f"Irons moved to appliances: {cur.rowcount}")

# 3. Move air coolers to appliances
cur.execute(
    "UPDATE products SET category = 'appliances', subcategory = 'coolers' "
    "WHERE category = 'kitchen_appliances' AND LOWER(name) LIKE '%air cooler%'"
)
print(f"Air coolers moved to appliances: {cur.rowcount}")

# 4. Move laundry baskets/bags to home_improvement
cur.execute(
    "UPDATE products SET category = 'home_improvement', subcategory = 'storage' "
    "WHERE category = 'kitchen_appliances' AND ("
    "  LOWER(name) LIKE '%laundry basket%' OR LOWER(name) LIKE '%laundry bag%'"
    ")"
)
print(f"Laundry items moved to home_improvement: {cur.rowcount}")

# 5. Move tiffin boxes and kadhai (cookware) to kitchen_essentials
cur.execute(
    "UPDATE products SET category = 'kitchen_essentials', subcategory = 'cookware' "
    "WHERE category = 'kitchen_appliances' AND ("
    "  LOWER(name) LIKE '%tiffin%' OR LOWER(name) LIKE '%kadhai%'"
    ")"
)
print(f"Tiffin/Kadhai moved to kitchen_essentials: {cur.rowcount}")

# 6. Move water purifiers to kitchen_essentials
cur.execute(
    "UPDATE products SET category = 'kitchen_essentials', subcategory = 'water_purifier' "
    "WHERE category = 'kitchen_appliances' AND LOWER(name) LIKE '%water purifier%'"
)
print(f"Water purifiers moved to kitchen_essentials: {cur.rowcount}")

conn.commit()
print()

# Verify final state
cur.execute("SELECT name, category FROM products WHERE category = 'kitchen_appliances' ORDER BY name")
rows = cur.fetchall()
print("=== Final kitchen_appliances ===")
for r in rows:
    print(f"  {r[0][:80]}")

print()
print("=== Check: ceiling fans now in appliances ===")
cur.execute("SELECT name, category FROM products WHERE LOWER(name) LIKE '%ceiling fan%'")
for r in cur.fetchall():
    print(f"  [{r[1]}] {r[0][:60]}")

print()
print("=== Check: laundry basket moved ===")
cur.execute("SELECT name, category FROM products WHERE LOWER(name) LIKE '%laundry basket%'")
for r in cur.fetchall():
    print(f"  [{r[1]}] {r[0][:60]}")

conn.close()
print("\nDone.")
