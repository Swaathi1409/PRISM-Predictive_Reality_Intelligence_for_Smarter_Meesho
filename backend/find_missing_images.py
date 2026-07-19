import sqlite3

conn = sqlite3.connect('app/data/prism_catalog.db')
cursor = conn.cursor()

# Products from user's request
search_products = [
    'Kundan Gold Plated Bridal Jewellery Set',
    'Orniza Kundan Necklace Set with Earrings Wedding Bridal',
    'Karatcraft 22KT Gold Plated Jhumka Earrings Traditional',
    '45L Laptop Backpack Water Resistant',
    'Rangoli Colour Powder 12 Shades 400g Set',
    'Clay Diyas Hand Painted Set of 20',
    'First Aid Travel Kit - 30-Piece Compact',
    'Cream Canvas Tote with Zipper',
    'Compact Dry Bag 10L Waterproof Roll-Top'
]

print('Searching for products in database:\n')

for product_name in search_products:
    # Try exact match first
    cursor.execute('SELECT id, name, image_url FROM products WHERE name = ?', (product_name,))
    row = cursor.fetchone()
    
    if not row:
        # Try partial match
        cursor.execute('SELECT id, name, image_url FROM products WHERE name LIKE ?', (f'%{product_name[:30]}%',))
        row = cursor.fetchone()
    
    if row:
        img_status = row[2] if row[2] else "NULL (local fallback)"
        print(f'✓ Found: {row[0]} | {row[1][:50]} | Image: {img_status[:60]}')
    else:
        print(f'✗ NOT FOUND: {product_name}')

conn.close()
