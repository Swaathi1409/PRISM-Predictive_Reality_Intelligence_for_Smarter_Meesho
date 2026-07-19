import sqlite3
import json
import os

list_path = 'product_list.txt'
db_path = 'app/data/prism_catalog.db'
json_path = 'app/data/mock_products.json'

with open(list_path, 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

mappings = []
for line in lines:
    parts = line.strip().split('\t')
    if len(parts) >= 5:
        img_full = parts[1].strip()
        img_name = img_full.replace('.jpg', '')
        category = parts[2].strip()
        prod_name = parts[4].strip()
        mappings.append((prod_name, img_name, category))

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

inserted_db = 0
updated_db = 0

for prod_name, img_name, category in mappings:
    image_url = f"/images/{img_name}.jpg"
    image_placeholder = img_name
    prod_id = img_name
    
    # Check if id already exists
    cursor.execute("SELECT id FROM products WHERE id = ?", (prod_id,))
    if cursor.fetchone():
        # Exists, so update it
        cursor.execute("UPDATE products SET name = ?, image_url = ?, image_placeholder = ? WHERE id = ?", 
                      (prod_name, image_url, image_placeholder, prod_id))
        updated_db += 1
        print(f"Updated existing ID in DB: {prod_id} -> {prod_name}")
    else:
        # Check if already updated by name or image_placeholder
        cursor.execute("SELECT id FROM products WHERE image_placeholder = ?", (image_placeholder,))
        if cursor.fetchone():
            continue
            
        cursor.execute("SELECT id FROM products WHERE name = ?", (prod_name,))
        if cursor.fetchone():
            continue

        # Insert to DB
        cursor.execute("""
        INSERT INTO products (
            id, name, category, subcategory, brand, price, original_price, discount_percent,
            seller_name, seller_rating, seller_review_count, seller_return_rate, delivery_days,
            available_pincodes, stock_status, price_trend_7d, tags, event_tags, description,
            image_url, image_placeholder
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prod_id, prod_name, category, category, 'Generic', 499, 999, 50,
            'Meesho Premium', 4.5, 150, 2.0, 3,
            json.dumps(["600001", "110001", "400001", "560001"]), 'IN_STOCK', json.dumps([]),
            json.dumps([category, 'premium']), json.dumps([]), f"High quality {prod_name}",
            image_url, image_placeholder
        ))
        inserted_db += 1
        print(f"Inserted to DB: {prod_name}")

conn.commit()
conn.close()

print(f"Inserted {inserted_db} new items, Updated {updated_db} items by ID.")

# JSON update can be done similarly, but since we are just making it work, 
# updating DB is the most important part because the backend reads from SQLite!
