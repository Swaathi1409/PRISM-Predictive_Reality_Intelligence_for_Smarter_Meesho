import sqlite3
import shutil
import os

conn = sqlite3.connect('app/data/prism_catalog.db')
cursor = conn.cursor()

# User-specified mappings
user_mappings = [
    ('Kundan Gold Plated Bridal Jewellery Set', 'WED001.jpg'),
    ('Orniza Kundan Necklace Set with Earrings Wedding Bridal', 'JWLRY004.jpg'),
    ('Karatcraft 22KT Gold Plated Jhumka Earrings Traditional', None),  # No mapping specified
    ('45L Laptop Backpack Water Resistant', 'BAG001.jpg'),
    ('Rangoli Colour Powder 12 Shades 400g Set', 'FES003.jpg'),
    ('Clay Diyas Hand Painted Set of 20', 'IMG_PROD_CLAY_DIYAS_100_SET_TERRACOTTA.jpg'),
    ('First Aid Travel Kit - 30-Piece Compact', 'TREK009.jpg'),
    ('Cream Canvas Tote with Zipper', 'BAG003.jpg'),
    ('Hostel Move-in Dorm Bedding & Essentials Kit', 'HOSTEL001.jpg'),
    ('Blue & White Laundry Bags (Set of 2)', 'IMG_PROD_LAUNDRY_BAG_SET_BLUE_WHITE.jpg'),
    ('Compact Dry Bag 10L Waterproof Roll-Top', 'TREK014.jpg'),
]

frontend_images_path = '../frontend/public/images'

print('Finding products in database and checking current status:\n')

for product_name, target_image in user_mappings:
    # Search for product by name
    cursor.execute('SELECT id, name, image_url FROM products WHERE name = ?', (product_name,))
    row = cursor.fetchone()
    
    if not row:
        # Try partial match
        cursor.execute('SELECT id, name, image_url FROM products WHERE name LIKE ?', (f'%{product_name[:30]}%',))
        row = cursor.fetchone()
    
    if row:
        pid, name, current_url = row
        has_amazon = current_url and (current_url.startswith('http') or current_url.startswith('//'))
        
        print(f'{pid}: {name[:50]}')
        print(f'  Current image_url: {current_url[:60] if current_url else "NULL"}')
        print(f'  Has Amazon URL: {"Yes" if has_amazon else "No"}')
        print(f'  Target image: {target_image if target_image else "Not specified"}')
        print()
    else:
        print(f'NOT FOUND: {product_name}')
        print()

conn.close()
