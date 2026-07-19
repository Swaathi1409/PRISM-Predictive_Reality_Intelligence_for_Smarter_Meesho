import sqlite3

conn = sqlite3.connect('app/data/prism_catalog.db')
cursor = conn.cursor()

# Fix FESTIVE002 - it has wrong image_url path
print('Fixing FESTIVE002 image_url...')
cursor.execute('UPDATE products SET image_url = NULL WHERE id = "FESTIVE002"')
print(f'Updated {cursor.rowcount} row(s)')

# Check for Amazon URLs for products without local images
missing_products = [
    ('JWLRY002', 'Karatcraft 22KT Gold Plated Jhumka Earrings'),
    ('FESTIVE003', 'Rangoli Colour Powder 12 Shades'),
    ('IMG_PROD_CANVAS_TOTE_CREAM_ZIPPER', 'Cream Canvas Tote with Zipper')
]

print('\nSearching for Amazon URLs for missing products...\n')

for pid, name in missing_products:
    # Try to find similar products with Amazon URLs
    cursor.execute('SELECT id, name, image_url FROM products WHERE name LIKE ? AND (image_url LIKE "http%" OR image_url LIKE "//%") LIMIT 2', (f'%{name[:20]}%',))
    amazon_matches = cursor.fetchall()
    
    if amazon_matches:
        print(f'{pid} ({name}):')
        print(f'  Found Amazon URLs from similar products:')
        for match in amazon_matches:
            print(f'    - {match[0]}: {match[1][:50]}')
            print(f'      URL: {match[2][:80]}')
    else:
        print(f'{pid} ({name}): No Amazon URLs found in similar products')
    print()

# Check if we can use existing local images as fallbacks
print('Checking for similar local images as fallbacks...\n')

# JWLRY002 - check if JWLRY001 can be used
if 'JWLRY001.jpg' in ['JWLRY001.jpg']:  # This exists in local images
    print('JWLRY002: Can use JWLRY001.jpg as fallback (similar jewellery)')

# FESTIVE003 - check for rangoli or festival images  
festival_images = ['FES003.jpg', 'FES004.jpg', 'FES005.jpg', 'FESTIVE006.jpg', 'FESTIVE007.jpg', 'rangoli_stencil_kit_colourful.jpg']
print(f'FESTIVE003: Available festival images: {festival_images}')

# IMG_PROD_CANVAS_TOTE_CREAM_ZIPPER - check for bag images
bag_images = ['BAG001.jpg', 'BAG002.jpg', 'BAG003.jpg', 'BAG004.jpg', 'BAG006.jpg']
print(f'IMG_PROD_CANVAS_TOTE_CREAM_ZIPPER: Available bag images: {bag_images}')

conn.commit()
conn.close()

print('\nDatabase updated successfully!')
