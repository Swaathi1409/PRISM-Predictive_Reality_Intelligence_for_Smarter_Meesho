import sqlite3
import json
import os

mappings = {
    "Kundan Gold Plated Bridal Jewellery Set": "JWLRY006",
    "Karatcraft 22KT Gold Plated Jhumka Earrings Traditional": "JWLRY007",
    "Orniza Kundan Necklace Set with Earrings Wedding Bridal": "JWLRY004",
    "45L Laptop Backpack Water Resistant": "BAG001",
    "Rangoli Colour Powder 12 Shades 400g Set": "FES003",
    "Clay Diyas Hand Painted Set of 20": "IMG_PROD_CLAY_DIYAS_100_SET_TERRACOTTA",
    "First Aid Travel Kit - 30-Piece Compact": "TREK009",
    "Cream Canvas Tote with Zipper": "BAG003",
    "Hostel Move-in Dorm Bedding & Essentials Kit": "HOSTEL001",
    "Blue & White Laundry Bags (Set of 2)": "IMG_PROD_LAUNDRY_BAG_SET_BLUE_WHITE",
    "Compact Dry Bag 10L Waterproof Roll-Top": "TREK014"
}

db_path = 'app/data/prism_catalog.db'
json_path = 'app/data/mock_products.json'

# Update DB
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

for name, img in mappings.items():
    image_url = f"/images/{img}.jpg"
    image_placeholder = img
    
    # Try exact match
    cursor.execute("SELECT id FROM products WHERE name = ?", (name,))
    row = cursor.fetchone()
    
    if row:
        cursor.execute("UPDATE products SET image_url = ?, image_placeholder = ? WHERE id = ?", (image_url, image_placeholder, row[0]))
        print(f"Updated DB for {name} (ID: {row[0]})")
    else:
        # Try LIKE match
        cursor.execute("SELECT id FROM products WHERE name LIKE ?", (f"%{name}%",))
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE products SET image_url = ?, image_placeholder = ? WHERE id = ?", (image_url, image_placeholder, row[0]))
            print(f"Updated DB (LIKE match) for {name} (ID: {row[0]})")
        else:
            print(f"Product NOT FOUND in DB: {name}")

conn.commit()
conn.close()

# Update JSON
if os.path.exists(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    updated = 0
    for p in products:
        for name, img in mappings.items():
            if name in p.get('name', ''):
                p['image_url'] = f"/images/{img}.jpg"
                p['image_placeholder'] = img
                updated += 1
                break
                
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2)
    print(f"Updated {updated} items in JSON.")
