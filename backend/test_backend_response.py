"""
Test what the backend actually returns when searching for bridal products.
"""
import sqlite3

conn = sqlite3.connect('app/data/prism_catalog.db')
cursor = conn.cursor()

print("Testing backend search for bridal products:\n")

# Search for products with "bridal" in name
cursor.execute('SELECT id, name, image_url FROM products WHERE name LIKE "%bridal%"')
bridal_products = cursor.fetchall()

print(f"Found {len(bridal_products)} products with 'bridal' in name:\n")

for pid, name, image_url in bridal_products:
    print(f"ID: {pid}")
    print(f"Name: {name}")
    print(f"Image URL: {image_url if image_url else 'NULL'}")
    print()

# Also search for "kundan" 
cursor.execute('SELECT id, name, image_url FROM products WHERE name LIKE "%kundan%"')
kundan_products = cursor.fetchall()

print(f"Found {len(kundan_products)} products with 'kundan' in name:\n")

for pid, name, image_url in kundan_products:
    print(f"ID: {pid}")
    print(f"Name: {name}")
    print(f"Image URL: {image_url if image_url else 'NULL'}")
    print()

# Check WED001 specifically
cursor.execute('SELECT id, name, image_url, category FROM products WHERE id = "WED001"')
wed001 = cursor.fetchone()

print("WED001 specific check:")
if wed001:
    print(f"ID: {wed001[0]}")
    print(f"Name: {wed001[1]}")
    print(f"Image URL: {wed001[2]}")
    print(f"Category: {wed001[3]}")
else:
    print("WED001 NOT FOUND")

conn.close()
