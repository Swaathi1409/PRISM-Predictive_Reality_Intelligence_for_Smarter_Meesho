import sys, json, sqlite3, os
sys.path.insert(0, ".")

db_path = "app/data/prism_catalog.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get all products sorted by trust signals
cur.execute("""
    SELECT id, name, image_url, seller_rating, seller_review_count, price, category, subcategory
    FROM products
    WHERE stock_status = 'in_stock'
    ORDER BY (seller_rating * LOG(MAX(seller_review_count, 1))) DESC
""")
rows = cur.fetchall()

amazon_imgs = []
non_amazon = []
no_image = []

for r in rows:
    img = r["image_url"] or ""
    if "amazon" in img.lower() or "m.media-amazon" in img.lower() or "images-na.ssl-images-amazon" in img.lower():
        amazon_imgs.append(dict(r))
    elif img.startswith("http"):
        non_amazon.append(dict(r))
    else:
        no_image.append(dict(r))

conn.close()

print(f"Total in-stock products: {len(rows)}")
print(f"Amazon images: {len(amazon_imgs)}")
print(f"Non-Amazon images: {len(non_amazon)}")
print(f"No/local image: {len(no_image)}")

print("\n=== NON-AMAZON IMAGE SOURCES ===")
sources = {}
for p in non_amazon:
    url = p["image_url"] or ""
    domain = url.split("/")[2] if url.startswith("http") else "none"
    sources[domain] = sources.get(domain, 0) + 1
for domain, count in sorted(sources.items(), key=lambda x: -x[1]):
    print(f"  {count}x  {domain}")
