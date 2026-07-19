import sqlite3

conn = sqlite3.connect('app/data/prism_catalog.db')
cursor = conn.cursor()

# Check current state
cursor.execute('SELECT COUNT(*) FROM products WHERE image_url IS NULL OR image_url = ""')
null_count = cursor.fetchone()[0]
print(f'Products with NULL/empty image_url (will use local fallback): {null_count}')

cursor.execute('SELECT COUNT(*) FROM products WHERE image_url LIKE "http%" OR image_url LIKE "//%"')
http_count = cursor.fetchone()[0]
print(f'Products with HTTP/protocol-relative URLs (Amazon CDN): {http_count}')

cursor.execute('SELECT COUNT(*) FROM products')
total_count = cursor.fetchone()[0]
print(f'Total products: {total_count}')

# Check specific products from user's list
test_ids = ['TREK001', 'HOSTEL001', 'HOSTEL002', 'ELEC001', 'BAG001']
print('\nSpecific products from user list:')
for pid in test_ids:
    cursor.execute('SELECT id, name, image_url FROM products WHERE id = ?', (pid,))
    row = cursor.fetchone()
    if row:
        img_status = "HTTP URL" if row[2] and (row[2].startswith('http') or row[2].startswith('//')) else "NULL (local fallback)" if not row[2] else f"Other: {row[2][:40]}"
        print(f'{row[0]}: {row[1][:40]} -> {img_status}')
    else:
        print(f'{pid}: NOT FOUND')

conn.close()
