"""
Test script for the automated image matching system.
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.image_matcher_service import get_image_matcher

def test_single_product_match():
    """Test matching a single product."""
    print("Testing single product image matching...\n")
    
    matcher = get_image_matcher()
    
    # Test with a product that needs image matching
    test_product_id = "TEST001"  # Use a test product
    
    # First, let's test with existing products
    test_products = [
        ("WED001", "Kundan Gold Plated Bridal Jewellery Set", "wedding_apparel"),
        ("NEW001", "Wireless Bluetooth Headphones Black", "electronics"),
        ("NEW002", "Cotton Saree with Golden Border", "formal_wear"),
    ]
    
    for pid, name, category in test_products:
        print(f"Testing: {pid} - {name}")
        result = matcher.match_image_for_product(pid, name, category)
        
        print(f"  Success: {result['success']}")
        print(f"  Source: {result['image_source']}")
        print(f"  Method: {result['method_used']}")
        print(f"  Image URL: {result['image_url'][:60] if result['image_url'] else 'None'}")
        print()

def test_batch_matching():
    """Test batch matching multiple products."""
    print("Testing batch image matching...\n")
    
    matcher = get_image_matcher()
    
    test_ids = ["WED001", "BAG001", "ELEC001", "NEW001", "NEW002"]
    
    results = matcher.batch_match_images(test_ids)
    
    for pid, result in results.items():
        print(f"{pid}:")
        print(f"  Success: {result.get('success', False)}")
        print(f"  Source: {result.get('image_source', 'N/A')}")
        print(f"  Method: {result.get('method_used', 'N/A')}")
        if result.get('error'):
            print(f"  Error: {result['error']}")
        print()

def test_fuzzy_search():
    """Test the fuzzy search functionality."""
    print("Testing fuzzy search for Amazon URLs...\n")
    
    matcher = get_image_matcher()
    
    # Test with different product names
    test_searches = [
        ("Gold Plated Earrings Traditional", "jewellery"),
        ("Canvas Tote Bag for Women", "bags_luggage"),
        ("Rangoli Colour Powder Set", "festival_decor"),
    ]
    
    for name, category in test_searches:
        print(f"Searching: {name} (Category: {category})")
        similar = matcher._find_similar_products_with_amazon_urls(name, category)
        
        if similar:
            print(f"  Found {len(similar)} similar products:")
            for pid, pname, url in similar[:3]:
                print(f"    - {pid}: {pname[:40]}")
                print(f"      URL: {url[:60]}")
        else:
            print("  No similar products found")
        print()

def test_local_fallback():
    """Test local image fallback creation."""
    print("Testing local image fallback...\n")
    
    matcher = get_image_matcher()
    
    test_cases = [
        ("TEST001", "Gold Necklace Set", "jewellery"),
        ("TEST002", "Laptop Backpack", "bags_luggage"),
        ("TEST003", "Festival Rangoli Kit", "festival_decor"),
    ]
    
    for pid, name, category in test_cases:
        print(f"Testing fallback for: {pid} - {name}")
        fallback = matcher._find_local_image_fallback(pid, name, category)
        
        if fallback:
            print(f"  Fallback found: {fallback}")
        else:
            print("  No fallback available")
        print()

if __name__ == "__main__":
    print("=" * 60)
    print("AUTOMATED IMAGE MATCHING SYSTEM TEST")
    print("=" * 60)
    print()
    
    # Run tests
    test_fuzzy_search()
    print("\n" + "=" * 60 + "\n")
    
    test_local_fallback()
    print("\n" + "=" * 60 + "\n")
    
    test_single_product_match()
    print("\n" + "=" * 60 + "\n")
    
    print("✓ All tests completed!")
