import sys, sqlite3, math
sys.path.insert(0, ".")

db_path = "app/data/prism_catalog.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT id, name, image_url, seller_rating, seller_review_count, price, category, subcategory
    FROM products
    WHERE stock_status = 'in_stock'
    ORDER BY (seller_rating * LOG(MAX(seller_review_count, 1))) DESC
""")
rows = cur.fetchall()
conn.close()

# Products needing local images (no valid image_url)
needs_image = [dict(r) for r in rows if not (r["image_url"] or "").startswith("http")]

# Products with Amazon images (keep as-is)
has_amazon = [dict(r) for r in rows if "amazon" in (r["image_url"] or "").lower()]

print(f"Products WITH Amazon images (keep as-is): {len(has_amazon)}")
print(f"Products NEEDING local images to generate: {len(needs_image)}")
print(f"\n=== PRODUCTS NEEDING LOCAL IMAGES (highest trust score first) ===")
print(f"{'#':<4} {'Score':<6} {'ID':<25} {'Cat':<20} {'Name'}")
print("-"*120)

for i, p in enumerate(needs_image, 1):
    rating = p["seller_rating"] or 0
    reviews = p["seller_review_count"] or 1
    score = round(rating * math.log1p(reviews), 1)
    pid = p["id"][:24]
    cat = p["category"][:19]
    name = (p["name"] or "")[:60]
    print(f"{i:<4} {score:<6} {pid:<25} {cat:<20} {name}")
