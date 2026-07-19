"""
Simple test script for the image matching service (standalone version).
"""
import sqlite3
import os
from difflib import SequenceMatcher

# Configuration
DB_PATH = "app/data/prism_catalog.db"
FRONTEND_IMAGES_PATH = "../frontend/public/images"

def fuzzy_match_score(str1, str2):
    """Calculate similarity score between two strings (0-1)."""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def find_similar_products_with_amazon_urls(product_name, category, limit=5):
    """Find similar products that have Amazon URLs."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Extract key words from product name
    words = [w.lower() for w in product_name.split() if len(w) > 3]
    
    # Build SQL query with multiple LIKE conditions
    conditions = []
    params = []
    
    for word in words[:4]:  # Use first 4 meaningful words
        conditions.append("name LIKE ?")
        params.append(f"%{word}%")
    
    if category:
        conditions.append("category = ?")
        params.append(category)
    
    conditions.append("(image_url LIKE 'http%' OR image_url LIKE '//%')")
    
    query = f"""
        SELECT id, name, image_url 
        FROM products 
        WHERE {' AND '.join(conditions)}
        LIMIT {limit}
    """
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    
    # Score by name similarity
    scored = []
    for pid, name, url in results:
        score = fuzzy_match_score(product_name, name)
        scored.append((score, pid, name, url))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(pid, name, url) for _, pid, name, url in scored]

def get_local_images():
    """Get set of available local image filenames."""
    if os.path.exists(FRONTEND_IMAGES_PATH):
        return set(
            f for f in os.listdir(FRONTEND_IMAGES_PATH) 
            if f.endswith('.jpg') or f.endswith('.png')
        )
    return set()

def test_fuzzy_search():
    """Test the fuzzy search functionality."""
    print("Testing fuzzy search for Amazon URLs...\n")
    
    # Test with different product names
    test_searches = [
        ("Gold Plated Earrings Traditional", "jewellery"),
        ("Canvas Tote Bag for Women", "bags_luggage"),
        ("Rangoli Colour Powder Set", "festival_decor"),
        ("Wireless Bluetooth Headphones", "electronics"),
    ]
    
    for name, category in test_searches:
        print(f"Searching: {name} (Category: {category})")
        similar = find_similar_products_with_amazon_urls(name, category)
        
        if similar:
            print(f"  Found {len(similar)} similar products:")
            for pid, pname, url in similar[:3]:
                score = fuzzy_match_score(name, pname)
                print(f"    - {pid}: {pname[:40]} (similarity: {score:.2f})")
                print(f"      URL: {url[:60]}")
        else:
            print("  No similar products found")
        print()

def test_local_images():
    """Test local image availability."""
    print("Testing local image availability...\n")
    
    local_images = get_local_images()
    print(f"Total local images available: {len(local_images)}")
    
    # Check for specific product images
    test_ids = ["WED001", "JWLRY004", "BAG001", "TREK009"]
    
    for pid in test_ids:
        if f"{pid}.jpg" in local_images:
            print(f"✓ {pid}.jpg exists")
        else:
            print(f"✗ {pid}.jpg missing")
    
    print()

def test_image_stats():
    """Test database image statistics."""
    print("Testing database image statistics...\n")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total products
    cursor.execute('SELECT COUNT(*) FROM products')
    total = cursor.fetchone()[0]
    
    # Products with Amazon URLs
    cursor.execute('SELECT COUNT(*) FROM products WHERE image_url LIKE "http%" OR image_url LIKE "//%"')
    amazon_count = cursor.fetchone()[0]
    
    # Products without images (NULL or empty)
    cursor.execute('SELECT COUNT(*) FROM products WHERE image_url IS NULL OR image_url = ""')
    no_image_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"Total products: {total}")
    print(f"With Amazon URLs: {amazon_count}")
    print(f"Without images: {no_image_count}")
    print(f"Image coverage: {((total - no_image_count) / total * 100):.1f}%")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("AUTOMATED IMAGE MATCHING SYSTEM TEST (SIMPLE)")
    print("=" * 60)
    print()
    
    # Run tests
    test_image_stats()
    print("=" * 60 + "\n")
    
    test_local_images()
    print("=" * 60 + "\n")
    
    test_fuzzy_search()
    print("=" * 60 + "\n")
    
    print("✓ All tests completed!")
