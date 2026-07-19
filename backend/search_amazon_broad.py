import sqlite3

conn = sqlite3.connect('app/data/prism_catalog.db')
cursor = conn.cursor()

# Search more broadly for Amazon URLs
print('Broad search for Amazon URLs by category and keywords:\n')

# JWLRY002 - Jewellery with "jhumka" or "earring"
cursor.execute('SELECT id, name, image_url FROM products WHERE (name LIKE "%jhumka%" OR name LIKE "%earring%" OR name LIKE "%earrings%") AND (image_url LIKE "http%" OR image_url LIKE "//%") LIMIT 5')
print('Jewellery with Amazon URLs (jhumka/earring):')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1][:50]} -> {row[2][:60]}')

# FESTIVE003 - Festival with "rangoli" or "colour" or "powder"  
cursor.execute('SELECT id, name, image_url FROM products WHERE (name LIKE "%rangoli%" OR name LIKE "%colour%" OR name LIKE "%powder%") AND (image_url LIKE "http%" OR image_url LIKE "//%") LIMIT 5')
print('\nFestival items with Amazon URLs (rangoli/colour/powder):')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1][:50]} -> {row[2][:60]}')

# IMG_PROD_CANVAS_TOTE_CREAM_ZIPPER - Bags with "tote" or "canvas"
cursor.execute('SELECT id, name, image_url FROM products WHERE (name LIKE "%tote%" OR name LIKE "%canvas%") AND (image_url LIKE "http%" OR image_url LIKE "//%") LIMIT 5')
print('\nBags with Amazon URLs (tote/canvas):')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1][:50]} -> {row[2][:60]}')

# Also check if there are any products with these exact names that have Amazon URLs
print('\n\nExact name search for Amazon URLs:\n')

search_terms = [
    ('JWLRY002', '%Karatcraft%'),
    ('FESTIVE003', '%Rangoli%'),
    ('IMG_PROD_CANVAS_TOTE_CREAM_ZIPPER', '%Canvas%Tote%')
]

for pid, pattern in search_terms:
    cursor.execute('SELECT id, name, image_url FROM products WHERE name LIKE ? AND (image_url LIKE "http%" OR image_url LIKE "//%") LIMIT 3', (pattern,))
    results = cursor.fetchall()
    if results:
        print(f'{pid} matches:')
        for row in results:
            print(f'  {row[0]}: {row[1][:50]} -> {row[2][:60]}')
    else:
        print(f'{pid}: No matches found')

conn.close()
