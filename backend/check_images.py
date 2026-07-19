import sqlite3

conn = sqlite3.connect('app/data/prism_catalog.db')
cursor = conn.cursor()

# Check for CDN/HTTP URLs
cursor.execute('SELECT COUNT(*) FROM products WHERE image_url LIKE "%http%" OR image_url LIKE "%amazon%" OR image_url LIKE "%cdn%"')
print('Products with CDN/HTTP URLs:', cursor.fetchone()[0])

# Check for local/missing image URLs
cursor.execute('SELECT COUNT(*) FROM products WHERE image_url IS NULL OR image_url = "" OR image_url LIKE "/images/%"')
print('Products with local/missing image URLs:', cursor.fetchone()[0])

# Total products
cursor.execute('SELECT COUNT(*) FROM products')
print('Total products:', cursor.fetchone()[0])

# Check specific products from the user's list
test_ids = ['TREK001', 'HOSTEL001', 'HOSTEL002', 'ELEC001', 'ELEC002']
for pid in test_ids:
    cursor.execute('SELECT id, name, image_url, stock_status FROM products WHERE id = ?', (pid,))
    row = cursor.fetchone()
    if row:
        print(f'\n{row[0]}: {row[1][:50]}, Image: {row[2][:60] if row[2] else None}, Stock: {row[3]}')
    else:
        print(f'\n{pid}: NOT FOUND in database')

# Check all product IDs that match the patterns from user's list
cursor.execute('SELECT id FROM products WHERE id LIKE "TREK%" OR id LIKE "HOSTEL%" OR id LIKE "ELEC%" ORDER BY id')
rows = cursor.fetchall()
print('\nProduct IDs matching TREK%, HOSTEL%, ELEC% patterns:')
for row in rows:
    print(row[0])

# Check for products with incorrect image_url paths that should use local fallback
cursor.execute('SELECT id, name, image_url FROM products WHERE image_url LIKE "/images/categories/%" LIMIT 10')
print('\nProducts with incorrect /images/categories/ paths (should use local fallback):')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1][:40]}, Image: {row[2][:60]}')

# Fix the image_url paths to use the correct local fallback format
cursor.execute('UPDATE products SET image_url = NULL WHERE image_url LIKE "/images/categories/%"')
print(f'\nUpdated {cursor.rowcount} products to NULL image_url (will trigger local fallback)')

# Also fix products with placeholder.jpg that should use local images
cursor.execute('UPDATE products SET image_url = NULL WHERE image_url = "/images/placeholder.jpg"')
print(f'Updated {cursor.rowcount} products with placeholder.jpg to NULL')

# Add missing products from user's list (HOSTEL001, HOSTEL002)
missing_products = [
    ('HOSTEL001', 'Single Fitted Bedsheet Set', 'bedding', 'bedding', 899, 1299, 30, 'in_stock', 'Blue/White stripes, college dorm style'),
    ('HOSTEL002', 'Toiletry Organizer Bag', 'personal_care', 'personal_care', 599, 899, 33, 'in_stock', 'Grey hanging organizer with mesh pockets'),
]

for pid, name, category, subcategory, price, original_price, discount, stock, desc in missing_products:
    cursor.execute('INSERT OR IGNORE INTO products (id, name, category, subcategory, price, original_price, discount_percent, stock_status, description, seller_name, seller_rating, seller_review_count, seller_return_rate, image_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (pid, name, category, subcategory, price, original_price, discount, stock, desc, 'PRISM Catalog', 4.2, 150, 5.0, None))
    print(f'Added {pid}: {name}')

conn.commit()
print('\nDatabase updated successfully!')

# Verify the updates
cursor.execute('SELECT COUNT(*) FROM products WHERE image_url IS NULL OR image_url = ""')
print(f'Products with NULL/empty image_url (will use local fallback): {cursor.fetchone()[0]}')

cursor.execute('SELECT id, name FROM products WHERE id IN ("HOSTEL001", "HOSTEL002")')
print('\nMissing products added:')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]}')

conn.close()
