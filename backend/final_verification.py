"""
Final verification that all changes are working correctly.
"""
import sqlite3
import os

conn = sqlite3.connect('app/data/prism_catalog.db')
cursor = conn.cursor()

frontend_images_path = '../frontend/public/images'

print("=" * 70)
print("FINAL VERIFICATION - ALL 11 USER-SPECIFIED PRODUCTS")
print("=" * 70)
print()

all_products = [
    ('WED001', 'Kundan Gold Plated Bridal Jewellery Set'),
    ('JWLRY004', 'Orniza Kundan Necklace Set with Earrings Wedding Bridal'),
    ('JWLRY002', 'Karatcraft 22KT Gold Plated Jhumka Earrings Traditional'),
    ('BAG001', '45L Laptop Backpack Water Resistant'),
    ('FESTIVE003', 'Rangoli Colour Powder 12 Shades 400g Set'),
    ('FESTIVE002', 'Clay Diyas Hand Painted Set of 20'),
    ('TREK009', 'First Aid Travel Kit - 30-Piece Compact'),
    ('IMG_PROD_CANVAS_TOTE_CREAM_ZIPPER', 'Cream Canvas Tote with Zipper'),
    ('UNIQ_HOSTEL', 'Hostel Move-in Dorm Bedding & Essentials Kit'),
    ('IMG_PROD_LAUNDRY_BAG_SET_BLUE_WHITE', 'Blue & White Laundry Bags (Set of 2)'),
    ('TREK014', 'Compact Dry Bag 10L Waterproof Roll-Top'),
]

all_ok = True

for pid, expected_name in all_products:
    cursor.execute('SELECT id, name, image_url FROM products WHERE id = ?', (pid,))
    row = cursor.fetchone()
    
    if not row:
        print(f"✗ {pid}: NOT FOUND IN DATABASE")
        all_ok = False
        continue
    
    actual_name = row[1]
    image_url = row[2]
    has_amazon = image_url and (image_url.startswith('http') or image_url.startswith('//'))
    has_local = os.path.exists(os.path.join(frontend_images_path, f'{pid}.jpg'))
    
    status = []
    if has_amazon:
        status.append('Amazon URL')
    if has_local:
        status.append('Local Image')
    if not has_amazon and not has_local:
        status.append('NO IMAGE')
    
    print(f"{pid}: {actual_name[:45]}")
    print(f"  Status: {', '.join(status)}")
    print(f"  Image URL: {image_url[:60] if image_url else 'NULL'}")
    print(f"  Local file: {'✓ Exists' if has_local else '✗ Missing'}")
    
    if not has_local and not has_amazon:
        print(f"  ⚠️  WARNING: This product has no image!")
        all_ok = False
    elif has_local:
        print(f"  ✓ Will display correctly via local fallback")
    elif has_amazon:
        print(f"  ✓ Will display via Amazon CDN")
    
    print()

print("=" * 70)
print("ADDITIONAL BRIDAL PRODUCTS (ENSURED TO HAVE IMAGES)")
print("=" * 70)
print()

additional_bridal = ['UNIQ_WEDDING', 'IMG_PROD_KUNDAN_BRIDAL_SET_GOLD', 'JWLRY003']

for pid in additional_bridal:
    cursor.execute('SELECT id, name, image_url FROM products WHERE id = ?', (pid,))
    row = cursor.fetchone()
    
    if row:
        has_local = os.path.exists(os.path.join(frontend_images_path, f'{pid}.jpg'))
        print(f"{pid}: {row[1][:45]}")
        print(f"  Local file: {'✓ Exists' if has_local else '✗ Missing'}")
        if has_local:
            print(f"  ✓ Will display correctly via local fallback")
        print()

conn.close()

print("=" * 70)
if all_ok:
    print("✓✓✓ ALL 11 PRODUCTS ARE PROPERLY CONFIGURED ✓✓✓")
    print("✓ Changes should reflect in frontend")
    print("✓ If not showing, restart frontend server")
else:
    print("✗✗✗ SOME PRODUCTS HAVE ISSUES ✗✗✗")
print("=" * 70)
