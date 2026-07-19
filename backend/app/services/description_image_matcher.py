"""
description_image_matcher.py — Enhanced image matching based on product descriptions.

This service matches product descriptions to image filenames using keyword extraction
and semantic matching. When a user asks for "bridal", it will find WED001.jpg (bridal jewellery).
"""

import sqlite3
import os
import re
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

class DescriptionImageMatcher:
    """Matches product descriptions to local image filenames."""
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), "../data/prism_catalog.db")
        self.frontend_images_path = os.path.join(os.path.dirname(__file__), "../../frontend/public/images")
        self._image_keywords_cache = None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from product name/description."""
        # Convert to lowercase and split
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Remove common words
        stop_words = {'the', 'and', 'for', 'with', 'set', 'kit', 'pack', 'piece', 'inch', 'cm', 'kg', 'g', 'ml', 'l'}
        keywords = [w for w in words if w not in stop_words]
        
        return keywords
    
    def _build_image_keyword_map(self) -> Dict[str, List[str]]:
        """Build a mapping of image filenames to their keywords."""
        if self._image_keywords_cache is not None:
            return self._image_keywords_cache
        
        keyword_map = {}
        
        if not os.path.exists(self.frontend_images_path):
            return keyword_map
        
        # Get all image files
        image_files = [f for f in os.listdir(self.frontend_images_path) if f.endswith(('.jpg', '.png'))]
        
        for img_file in image_files:
            # Extract keywords from filename
            name_without_ext = os.path.splitext(img_file)[0]
            # Convert underscores and hyphens to spaces
            name_normalized = name_without_ext.replace('_', ' ').replace('-', ' ')
            keywords = self._extract_keywords(name_normalized)
            
            keyword_map[img_file] = keywords
        
        self._image_keywords_cache = keyword_map
        return keyword_map
    
    def match_description_to_image(self, product_name: str, product_id: str = None) -> Optional[str]:
        """
        Match a product description to the best local image.
        
        Args:
            product_name: The product name/description
            product_id: Optional product ID for exact match check
            
        Returns:
            Image filename or None
        """
        # First check for exact ID match
        if product_id:
            exact_match = f"{product_id}.jpg"
            if os.path.exists(os.path.join(self.frontend_images_path, exact_match)):
                return exact_match
        
        # Extract keywords from product name
        product_keywords = self._extract_keywords(product_name)
        
        # Get image keyword map
        image_keyword_map = self._build_image_keyword_map()
        
        # Score each image by keyword overlap
        scored_images = []
        
        for img_file, img_keywords in image_keyword_map.items():
            # Calculate keyword overlap score
            overlap = len(set(product_keywords) & set(img_keywords))
            if overlap > 0:
                # Calculate similarity score
                score = overlap / max(len(product_keywords), len(img_keywords))
                scored_images.append((score, img_file, img_keywords))
        
        # Sort by score (highest first)
        scored_images.sort(key=lambda x: x[0], reverse=True)
        
        if scored_images:
            best_match = scored_images[0]
            return best_match[1]  # Return image filename
        
        return None
    
    def get_product_image_mapping(self, product_id: str, product_name: str) -> Dict[str, str]:
        """
        Get the complete image mapping for a product.
        
        Returns:
            Dict with image_source, image_path, and method_used
        """
        result = {
            'image_source': None,
            'image_path': None,
            'method_used': None
        }
        
        # Check database for Amazon URL
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT image_url FROM products WHERE id = ?', (product_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] and (row[0].startswith('http') or row[0].startswith('//')):
            result['image_source'] = 'amazon_url'
            result['image_path'] = row[0]
            result['method_used'] = 'existing_amazon_url'
            return result
        
        # Try description matching
        matched_image = self.match_description_to_image(product_name, product_id)
        
        if matched_image:
            result['image_source'] = 'local_fallback'
            result['image_path'] = f"/images/{matched_image}"
            result['method_used'] = f'description_match_{matched_image}'
            return result
        
        # No match found
        result['image_source'] = 'placeholder'
        result['image_path'] = None
        result['method_used'] = 'placeholder_fallback'
        
        return result
    
    def update_product_with_matched_image(self, product_id: str, product_name: str) -> bool:
        """
        Update a product in the database with its matched image.
        
        Returns:
            True if updated, False otherwise
        """
        mapping = self.get_product_image_mapping(product_id, product_name)
        
        if mapping['image_source'] == 'local_fallback':
            # Ensure the local image file exists for the product ID
            matched_image = mapping['image_path'].split('/')[-1]
            target_path = os.path.join(self.frontend_images_path, f"{product_id}.jpg")
            source_path = os.path.join(self.frontend_images_path, matched_image)
            
            if not os.path.exists(target_path) and os.path.exists(source_path):
                import shutil
                shutil.copy(source_path, target_path)
            
            # Update database to NULL (will use local fallback)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('UPDATE products SET image_url = NULL WHERE id = ?', (product_id,))
            conn.commit()
            conn.close()
            
            return True
        
        return False


# Singleton instance
_matcher = None

def get_description_matcher() -> DescriptionImageMatcher:
    """Get the singleton DescriptionImageMatcher instance."""
    global _matcher
    if _matcher is None:
        _matcher = DescriptionImageMatcher()
    return _matcher
