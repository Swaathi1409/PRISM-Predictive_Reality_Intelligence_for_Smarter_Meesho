import sqlite3
import os

conn = sqlite3.connect('app/data/prism_catalog.db')
cursor = conn.cursor()

frontend_images_path = '../frontend/public/images'

# All 11 products to verify
products_to_verify = [
    'WED001',
    'JWLRY004', 
    'JWLRY002',
    'BAG001',
    'FESTIVE003',
    'FESTIVE002',
    'TREK009',
    'IMG_PROD_CANVAS_TOTE_CREAM_ZIPPER',
    'UNIQ_HOSTEL',  # This is the HOSTEL product
    'IMG_PROD_LAUNDRY_BAG_SET_BLUE_WHITE',
    'TREK014'
]

print('Final verification of all 11 products:\n')

for pid in products_to_verify:
    cursor.execute('SELECT id, name, image_url FROM products WHERE id = ?', (pid,))
    row = cursor.fetchone()
    
    if row:
        pid, name, current_url = row
        has_amazon = current_url and (current_url.startswith('http') or current_url.startswith('//'))
        has_local = os.path.exists(os.path.join(frontend_images_path, f'{pid}.jpg'))
        
        status = []
        if has_amazon:
            status.append('Amazon URL')
        if has_local:
            status.append('Local image')
        if not has_amazon and not has_local:
            status.append('NULL (will use fallback)')
        
        print(f'{pid}: {name[:45]}')
        print(f'  Status: {", ".join(status)}')
        print(f'  Image URL: {current_url[:60] if current_url else "NULL"}')
        print(f'  Local file exists: {"Yes" if has_local else "No"}')
        
        # Special check for UNIQ_HOSTEL (the HOSTEL product)
        if pid == 'UNIQ_HOSTEL':
            print(f'  *** HOSTEL PRODUCT - This was the one not showing before ***')
            if has_local:
                print(f'  ✓ FIXED: Now has local image and should display correctly')
            else:
                print(f'  ✗ ISSUE: Still missing local image')
        
        print()
    else:
        print(f'✗ {pid}: NOT FOUND in database\n')

conn.close()

print('✓ Verification complete!')
