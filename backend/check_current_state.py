import sqlite3
import os

conn = sqlite3.connect('app/data/prism_catalog.db')
cursor = conn.cursor()

print("Checking current database state:\n")

# Check WED001 specifically
cursor.execute('SELECT id, name, image_url FROM products WHERE id = "WED001"')
wed_row = cursor.fetchone()
if wed_row:
    print(f"WED001: {wed_row[1]}")
    print(f"  image_url: {wed_row[2]}")
    print(f"  Has Amazon URL: {wed_row[2] and (wed_row[2].startswith('http') or wed_row[2].startswith('//'))}")
else:
    print("WED001: NOT FOUND")

# Check UNIQ_HOSTEL (the hostel product)
cursor.execute('SELECT id, name, image_url FROM products WHERE id = "UNIQ_HOSTEL"')
hostel_row = cursor.fetchone()
if hostel_row:
    print(f"\nUNIQ_HOSTEL: {hostel_row[1]}")
    print(f"  image_url: {hostel_row[2]}")
else:
    print("\nUNIQ_HOSTEL: NOT FOUND")

# Check all 11 products
all_products = [
    'WED001', 'JWLRY004', 'JWLRY002', 'BAG001', 
    'FESTIVE003', 'FESTIVE002', 'TREK009', 
    'IMG_PROD_CANVAS_TOTE_CREAM_ZIPPER', 'UNIQ_HOSTEL',
    'IMG_PROD_LAUNDRY_BAG_SET_BLUE_WHITE', 'TREK014'
]

print("\n\nAll 11 products status:")
print("-" * 60)

frontend_images_path = '../frontend/public/images'

for pid in all_products:
    cursor.execute('SELECT id, name, image_url FROM products WHERE id = ?', (pid,))
    row = cursor.fetchone()
    if row:
        has_amazon = row[2] and (row[2].startswith('http') or row[2].startswith('//'))
        has_local = os.path.exists(os.path.join(frontend_images_path, f'{pid}.jpg'))
        print(f"{pid}: {'Amazon' if has_amazon else 'Local' if has_local else 'None'}")
    else:
        print(f"{pid}: NOT FOUND")

conn.close()

# Check if WED001.jpg exists
print("\n\nChecking WED001.jpg in frontend:")
wed001_path = os.path.join(frontend_images_path, 'WED001.jpg')
if os.path.exists(wed001_path):
    print(f"✓ WED001.jpg exists at {wed001_path}")
    print(f"  Size: {os.path.getsize(wed001_path)} bytes")
else:
    print(f"✗ WED001.jpg NOT FOUND at {wed001_path}")
