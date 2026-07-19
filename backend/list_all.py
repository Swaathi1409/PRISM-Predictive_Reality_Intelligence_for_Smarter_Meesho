import sys, sqlite3, math
sys.path.insert(0, ".")
db_path = "app/data/prism_catalog.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("""
    SELECT id, name, image_url, seller_rating, seller_review_count, category, subcategory
    FROM products WHERE stock_status = "in_stock"
    ORDER BY (seller_rating * LOG(MAX(seller_review_count, 1))) DESC
""")
rows = cur.fetchall()
conn.close()
needs_image = [dict(r) for r in rows if not (r["image_url"] or "").startswith("http")]
print(f"Total: {len(needs_image)}")
for i, p in enumerate(needs_image, 1):
    rating = p["seller_rating"] or 0
    reviews = p["seller_review_count"] or 1
    score = round(rating * math.log1p(reviews), 1)
    print(f"{i}|{p['id']}|{p['category']}|{p['subcategory']}|{score}|{(p['name'] or '')[:80]}")
