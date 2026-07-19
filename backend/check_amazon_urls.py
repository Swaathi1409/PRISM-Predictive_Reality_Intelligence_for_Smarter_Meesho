import sqlite3

conn = sqlite3.connect('app/data/prism_catalog.db')
cursor = conn.cursor()

# Products without local images
missing_image_products = [
    'JWLRY002',  # Karatcraft 22KT Gold Plated Jhumka Earrings Traditional
    'FESTIVE003', # Rangoli Colour Powder 12 Shades 400g Set
    'FESTIVE002', # Clay Diyas Hand Painted Set of 20
    'IMG_PROD_CANVAS_TOTE_CREAM_ZIPPER' # Cream Canvas Tote with Zipper
]

print('Checking for Amazon URLs and alternatives:\n')

for pid in missing_image_products:
    cursor.execute('SELECT id, name, image_url, category FROM products WHERE id = ?', (pid,))
    row = cursor.fetchone()
    
    if row:
        has_amazon = row[2] and (row[2].startswith('http') or row[2].startswith('//'))
        print(f'{row[0]}: {row[1][:50]}')
        print(f'  Category: {row[3]}')
        print(f'  Current image_url: {row[2][:80] if row[2] else "NULL"}')
        print(f'  Has Amazon URL: {"Yes" if has_amazon else "No"}')
        
        # Look for similar products with Amazon URLs in same category
        cursor.execute('SELECT id, name, image_url FROM products WHERE category = ? AND (image_url LIKE "http%" OR image_url LIKE "//%") LIMIT 3', (row[3],))
        similar = cursor.fetchall()
        if similar:
            print(f'  Similar products with Amazon URLs:')
            for s in similar:
                print(f'    - {s[0]}: {s[1][:40]}')
        print()
    else:
        print(f'{pid}: NOT FOUND in database\n')

conn.close()
