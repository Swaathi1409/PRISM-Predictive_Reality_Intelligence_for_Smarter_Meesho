import sqlite3
import shutil
import os

conn = sqlite3.connect('app/data/prism_catalog.db')
cursor = conn.cursor()

frontend_images_path = '../frontend/public/images'

# Mappings: (product_id, target_image_filename)
mappings = [
    ('WED001', 'WED001.jpg'),
    ('JWLRY004', 'JWLRY004.jpg'),
    ('JWLRY002', None),  # Keep Amazon URL
    ('BAG001', 'BAG001.jpg'),
    ('FESTIVE003', 'FES003.jpg'),
    ('FESTIVE002', 'IMG_PROD_CLAY_DIYAS_100_SET_TERRACOTTA.jpg'),
    ('TREK009', 'TREK009.jpg'),
    ('IMG_PROD_CANVAS_TOTE_CREAM_ZIPPER', 'BAG003.jpg'),
    ('UNIQ_HOSTEL', 'HOSTEL001.jpg'),  # Important: HOSTEL001 is stored as UNIQ_HOSTEL
    ('IMG_PROD_LAUNDRY_BAG_SET_BLUE_WHITE', 'IMG_PROD_LAUNDRY_BAG_SET_BLUE_WHITE.jpg'),
    ('TREK014', 'TREK014.jpg'),
]

# Also fix products that already have the correct local image but wrong image_url in DB
fix_image_url_to_null = [
    'WED001',
    'JWLRY004', 
    'BAG001',
    'TREK009',
    'TREK014',
    'IMG_PROD_LAUNDRY_BAG_SET_BLUE_WHITE',  # Has wrong path, needs to be NULL
]

print('Applying user-specified image mappings:\n')

for pid, target_image in mappings:
    if target_image is None:
        print(f'{pid}: Skipping (no mapping specified)')
        continue
    
    # Check if target image exists in frontend
    target_path = os.path.join(frontend_images_path, target_image)
    if not os.path.exists(target_path):
        print(f'✗ {pid}: Target image {target_image} NOT FOUND in frontend')
        continue
    
    # Create local image copy for the product
    product_image_path = os.path.join(frontend_images_path, f'{pid}.jpg')
    
    try:
        shutil.copy(target_path, product_image_path)
        print(f'✓ Created {pid}.jpg (copy of {target_image})')
        
        # Update database to remove Amazon URL and set to NULL (will use local fallback)
        cursor.execute('UPDATE products SET image_url = NULL WHERE id = ?', (pid,))
        print(f'  Updated database: image_url set to NULL for {pid}')
        
    except Exception as e:
        print(f'✗ {pid}: Failed to create image - {e}')
    
    print()

# Fix products that already have correct local images but wrong image_url in DB
print('\nFixing image_url for products with correct local images:\n')

for pid in fix_image_url_to_null:
    cursor.execute('UPDATE products SET image_url = NULL WHERE id = ?', (pid,))
    if cursor.rowcount > 0:
        print(f'✓ Fixed {pid}: image_url set to NULL (will use local fallback)')
    else:
        print(f'- {pid}: No changes needed or not found')

conn.commit()
conn.close()

print('\n✓ All mappings applied successfully!')
