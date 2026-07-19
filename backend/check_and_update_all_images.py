import sqlite3
import json
import os
import re

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
        prod_name = parts[4].strip()
        mappings.append((prod_name, img_name))

# Update DB
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

not_found = []
updated_db = 0

for prod_name, img_name in mappings:
    image_url = f"/images/{img_name}.jpg"
    image_placeholder = img_name
    
    # Check if already updated
    cursor.execute("SELECT id, name, image_placeholder FROM products WHERE image_placeholder = ?", (image_placeholder,))
    if cursor.fetchone():
        continue
    
    # Try exact match first
    cursor.execute("SELECT id, name, image_placeholder FROM products WHERE name = ?", (prod_name,))
    row = cursor.fetchone()
    
    if not row:
        short_name = re.split(r'[-—–\ufffd]', prod_name)[0].strip()
        words = short_name.split()
        if len(words) >= 3:
            search_term = " ".join(words[:3])
        else:
            search_term = short_name
            
        cursor.execute("SELECT id, name, image_placeholder FROM products WHERE name LIKE ?", (f"%{search_term}%",))
        row = cursor.fetchone()

        if not row and len(words) >= 2:
            search_term = " ".join(words[:2])
            cursor.execute("SELECT id, name, image_placeholder FROM products WHERE name LIKE ?", (f"%{search_term}%",))
            row = cursor.fetchone()

    if row:
        if row[2] != image_placeholder:
            cursor.execute("UPDATE products SET image_url = ?, image_placeholder = ? WHERE id = ?", (image_url, image_placeholder, row[0]))
            updated_db += 1
            print(f"Updated DB: {row[1]} -> {img_name}")
    else:
        not_found.append(prod_name)

conn.commit()
conn.close()

print(f"Updated {updated_db} NEW items in DB.")
if not_found:
    print(f"{len(not_found)} items STILL not found in DB:")
    for nf in not_found:
        print(f"  - {nf}")
else:
    print("All items mapped successfully in DB!")
