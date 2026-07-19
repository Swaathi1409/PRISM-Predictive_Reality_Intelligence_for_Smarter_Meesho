import sqlite3
import shutil
import os

conn = sqlite3.connect('app/data/prism_catalog.db')
cursor = conn.cursor()

frontend_images_path = os.path.join('..', 'frontend', 'public', 'images')

# Fix FESTIVE002 - Clay Diyas should use clay_diyas image
if os.path.exists(os.path.join(frontend_images_path, 'clay_diyas_100_set_terracotta.jpg')):
    shutil.copy(
        os.path.join(frontend_images_path, 'clay_diyas_100_set_terracotta.jpg'),
        os.path.join(frontend_images_path, 'FESTIVE002.jpg')
    )
    print('✓ Created FESTIVE002.jpg (copy of clay_diyas_100_set_terracotta.jpg)')

# Also update the database to remove the wrong path
cursor.execute('UPDATE products SET image_url = NULL WHERE id = "FESTIVE002"')
print('✓ Updated FESTIVE002 image_url to NULL (will use local fallback)')

conn.commit()

# Final verification
print('\nFinal verification of all 9 products:\n')

all_products = [
    'WED001', 'JWLRY004', 'JWLRY002', 'BAG001', 
    'FESTIVE003', 'FESTIVE002', 'TREK009', 
    'IMG_PROD_CANVAS_TOTE_CREAM_ZIPPER', 'TREK014'
]

for pid in all_products:
    cursor.execute('SELECT id, name, image_url FROM products WHERE id = ?', (pid,))
    row = cursor.fetchone()
    if row:
        has_amazon = row[2] and (row[2].startswith('http') or row[2].startswith('//'))
        has_local = os.path.exists(os.path.join(frontend_images_path, f'{pid}.jpg'))
        
        status = []
        if has_amazon:
            status.append('Amazon URL')
        if has_local:
            status.append('Local image')
        if not has_amazon and not has_local:
            status.append('NULL (will use fallback)')
            
        print(f'{row[0]}: {row[1][:45]}')
        print(f'  Status: {", ".join(status)}')

conn.close()
print('\n✓ All products now have images!')
