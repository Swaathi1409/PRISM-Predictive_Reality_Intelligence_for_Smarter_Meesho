"""
Test the description-based image matcher.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

# Simple version without imports
import sqlite3
import re
from difflib import SequenceMatcher

def extract_keywords(text):
    """Extract meaningful keywords from product name/description."""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    stop_words = {'the', 'and', 'for', 'with', 'set', 'kit', 'pack', 'piece', 'inch', 'cm', 'kg', 'g', 'ml', 'l'}
    keywords = [w for w in words if w not in stop_words]
    return keywords

def build_image_keyword_map(frontend_images_path):
    """Build a mapping of image filenames to their keywords."""
    keyword_map = {}
    
    if not os.path.exists(frontend_images_path):
        return keyword_map
    
    image_files = [f for f in os.listdir(frontend_images_path) if f.endswith(('.jpg', '.png'))]
    
    for img_file in image_files:
        name_without_ext = os.path.splitext(img_file)[0]
        name_normalized = name_without_ext.replace('_', ' ').replace('-', ' ')
        keywords = extract_keywords(name_normalized)
        keyword_map[img_file] = keywords
    
    return keyword_map

def match_description_to_image(product_name, frontend_images_path):
    """Match a product description to the best local image."""
    product_keywords = extract_keywords(product_name)
    image_keyword_map = build_image_keyword_map(frontend_images_path)
    
    scored_images = []
    
    for img_file, img_keywords in image_keyword_map.items():
        overlap = len(set(product_keywords) & set(img_keywords))
        if overlap > 0:
            score = overlap / max(len(product_keywords), len(img_keywords))
            scored_images.append((score, img_file, img_keywords))
    
    scored_images.sort(key=lambda x: x[0], reverse=True)
    
    if scored_images:
        return scored_images[0]
    
    return None

# Test with bridal product
frontend_path = '../frontend/public/images'

print("Testing description-based image matching:\n")

test_products = [
    ("Kundan Gold Plated Bridal Jewellery Set", "WED001"),
    ("Orniza Kundan Necklace Set with Earrings Wedding Bridal", "JWLRY004"),
    ("Hostel Move-in Dorm Bedding & Essentials Kit", "UNIQ_HOSTEL"),
    ("45L Laptop Backpack Water Resistant", "BAG001"),
]

for product_name, expected_id in test_products:
    print(f"Product: {product_name}")
    print(f"Expected ID: {expected_id}")
    
    match = match_description_to_image(product_name, frontend_path)
    
    if match:
        score, img_file, keywords = match
        print(f"Matched: {img_file} (score: {score:.2f})")
        print(f"Image keywords: {keywords}")
        
        # Check if it matches expected
        if img_file == f"{expected_id}.jpg":
            print("✓ CORRECT MATCH")
        else:
            print(f"✗ MISMATCH - expected {expected_id}.jpg")
    else:
        print("✗ NO MATCH FOUND")
    
    print()

print("Testing specific keyword matching:\n")

# Test "bridal" keyword
bridal_match = match_description_to_image("bridal jewellery", frontend_path)
if bridal_match:
    print(f"'bridal' matched to: {bridal_match[1]}")
else:
    print("'bridal' no match")

# Test "hostel" keyword  
hostel_match = match_description_to_image("hostel essentials", frontend_path)
if hostel_match:
    print(f"'hostel' matched to: {hostel_match[1]}")
else:
    print("'hostel' no match")

# Test "backpack" keyword
backpack_match = match_description_to_image("laptop backpack", frontend_path)
if backpack_match:
    print(f"'backpack' matched to: {backpack_match[1]}")
else:
    print("'backpack' no match")
