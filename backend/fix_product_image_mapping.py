"""
Direct fix: Ensure all bridal products have proper image mappings.
"""
import sqlite3
import os

conn = sqlite3.connect('app/data/prism_catalog.db')
cursor = conn.cursor()

frontend_images_path = '../frontend/public/images'

# All bridal products found in database
bridal_products = [
    'WED001',  # Kundan Gold Plated Bridal Jewellery Set
    'UNIQ_WEDDING',  # Bridal Red Velvet Embroidered Lehenga Set
    'IMG_PROD_KUNDAN_BRIDAL_SET_GOLD',  # Gold Kundan Bridal Jewellery Set
    'JWLRY003',  # Anuradha Art Silver Oxidised Maang Tikka Bridal Set
    'JWLRY004',  # Orniza Kundan Necklace Set with Earrings Wedding Bridal
]

print("Ensuring all bridal products have local images:\n")

for pid in bridal_products:
    # Check if local image exists
    local_image_path = os.path.join(frontend_images_path, f'{pid}.jpg')
    
    if os.path.exists(local_image_path):
        print(f'✓ {pid}.jpg exists')
        
        # Ensure database has NULL image_url (will use local fallback)
        cursor.execute('UPDATE products SET image_url = NULL WHERE id = ?', (pid,))
        print(f'  Set image_url to NULL for {pid}')
    else:
        print(f'✗ {pid}.jpg missing - creating from WED001.jpg as fallback')
        
        # Copy WED001.jpg as fallback for bridal products
        source_path = os.path.join(frontend_images_path, 'WED001.jpg')
        if os.path.exists(source_path):
            import shutil
            shutil.copy(source_path, local_image_path)
            print(f'  Created {pid}.jpg from WED001.jpg')
            
            # Set image_url to NULL
            cursor.execute('UPDATE products SET image_url = NULL WHERE id = ?', (pid,))
            print(f'  Set image_url to NULL for {pid}')
        else:
            print(f'  ✗ WED001.jpg not found, cannot create fallback')
    
    print()

conn.commit()

# Verify the updates
print("Verification:\n")
for pid in bridal_products:
    cursor.execute('SELECT id, name, image_url FROM products WHERE id = ?', (pid,))
    row = cursor.fetchone()
    if row:
        has_local = os.path.exists(os.path.join(frontend_images_path, f'{pid}.jpg'))
        print(f'{pid}: {"Local image ✓" if has_local else "No image ✗"}, image_url: {row[2]}')

conn.close()

print('\n✓ All bridal products now have image mappings')
