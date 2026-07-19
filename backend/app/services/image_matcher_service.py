"""
image_matcher_service.py — Automated image matching service for PRISM.

This service provides on-demand image matching for products that don't have images.
It uses fuzzy string matching, category-based similarity, and automatic fallback creation.

MATCHING STRATEGY:
1. Exact ID match → use existing local image
2. Fuzzy name match → find similar product with Amazon URL
3. Category-based match → use Amazon URL from similar category product
4. Local image fallback → copy from similar product's local image
5. Placeholder → use generic placeholder as last resort

USAGE:
    from app.services.image_matcher_service import ImageMatcherService
    matcher = ImageMatcherService()
    result = matcher.match_image_for_product(product_id, product_name, category)
"""

import os
import sqlite3
import shutil
from typing import Optional, Dict, List, Tuple
from difflib import SequenceMatcher
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ImageMatcherService:
    """Service for automatically matching and creating product images."""
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), "../data/prism_catalog.db")
        self.frontend_images_path = os.path.join(os.path.dirname(__file__), "../../frontend/public/images")
        self._local_images_cache = None
    
    def _get_local_images(self) -> set:
        """Get set of available local image filenames."""
        if self._local_images_cache is None:
            if os.path.exists(self.frontend_images_path):
                self._local_images_cache = set(
                    f for f in os.listdir(self.frontend_images_path) 
                    if f.endswith('.jpg') or f.endswith('.png')
                )
            else:
                self._local_images_cache = set()
        return self._local_images_cache
    
    def _fuzzy_match_score(self, str1: str, str2: str) -> float:
        """Calculate similarity score between two strings (0-1)."""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def _find_similar_products_with_amazon_urls(
        self, 
        product_name: str, 
        category: str,
        limit: int = 5
    ) -> List[Tuple[str, str, str]]:
        """Find similar products that have Amazon URLs.
        
        Returns: List of (product_id, product_name, amazon_url)
        """
        conn = sqlite3.connect(self.db_path)
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
            score = self._fuzzy_match_score(product_name, name)
            scored.append((score, pid, name, url))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [(pid, name, url) for _, pid, name, url in scored]
    
    def _find_local_image_fallback(
        self, 
        product_id: str, 
        product_name: str, 
        category: str
    ) -> Optional[str]:
        """Find a local image to use as fallback."""
        local_images = self._get_local_images()
        
        # Check for exact ID match
        if f"{product_id}.jpg" in local_images:
            return f"/images/{product_id}.jpg"
        
        # Check for similar local images by name keywords
        words = [w.lower() for w in product_name.split() if len(w) > 3]
        
        for img in local_images:
            img_name = img.replace('.jpg', '').replace('.png', '').lower()
            for word in words:
                if word in img_name or img_name in word:
                    return f"/images/{img}"
        
        # Check category-based fallback
        category_images = {
            'jewellery': ['JWLRY001.jpg', 'JWLRY004.jpg'],
            'bags_luggage': ['BAG001.jpg', 'BAG002.jpg', 'BAG003.jpg'],
            'festival_decor': ['FES003.jpg', 'FESTIVE006.jpg', 'rangoli_stencil_kit_colourful.jpg'],
            'bedding': ['BED002.jpg', 'BED004.jpg'],
            'electronics': ['ELEC001.jpg', 'ELEC002.jpg'],
            'formal_wear': ['FORMAL001.jpg', 'FORMAL002.jpg'],
        }
        
        if category in category_images:
            for fallback_img in category_images[category]:
                if fallback_img in local_images:
                    return f"/images/{fallback_img}"
        
        return None
    
    def _create_local_image_copy(
        self, 
        source_image: str, 
        target_product_id: str
    ) -> bool:
        """Copy a local image for the target product."""
        try:
            source_path = os.path.join(self.frontend_images_path, source_image)
            target_path = os.path.join(self.frontend_images_path, f"{target_product_id}.jpg")
            
            if os.path.exists(source_path):
                shutil.copy(source_path, target_path)
                logger.info(f"Created local image: {target_product_id}.jpg (copy of {source_image})")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to create local image copy: {e}")
            return False
    
    def match_image_for_product(
        self,
        product_id: str,
        product_name: str,
        category: str = None
    ) -> Dict[str, any]:
        """
        Main method to match and assign an image for a product.
        
        Returns dict with:
            - success: bool
            - image_source: str ('amazon_url', 'local_fallback', 'placeholder')
            - image_url: str or None
            - method_used: str describing the matching strategy
        """
        result = {
            'success': False,
            'image_source': None,
            'image_url': None,
            'method_used': None
        }
        
        logger.info(f"Matching image for {product_id}: {product_name[:50]}")
        
        # Strategy 1: Check if product already has Amazon URL
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT image_url FROM products WHERE id = ?', (product_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] and (row[0].startswith('http') or row[0].startswith('//')):
            result['success'] = True
            result['image_source'] = 'amazon_url'
            result['image_url'] = row[0]
            result['method_used'] = 'existing_amazon_url'
            logger.info(f"Using existing Amazon URL for {product_id}")
            return result
        
        # Strategy 2: Find similar products with Amazon URLs
        similar_amazon = self._find_similar_products_with_amazon_urls(product_name, category)
        if similar_amazon:
            best_match = similar_amazon[0]
            amazon_url = best_match[2]  # URL is at index 2
            
            # Update database with Amazon URL
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('UPDATE products SET image_url = ? WHERE id = ?', (amazon_url, product_id))
            conn.commit()
            conn.close()
            
            result['success'] = True
            result['image_source'] = 'amazon_url'
            result['image_url'] = amazon_url
            result['method_used'] = f'similar_amazon_match_{best_match[0]}'
            logger.info(f"Assigned Amazon URL from {best_match[0]} to {product_id}")
            return result
        
        # Strategy 3: Find local image fallback
        local_fallback = self._find_local_image_fallback(product_id, product_name, category)
        if local_fallback:
            # Extract filename from path
            source_image = local_fallback.split('/')[-1]
            
            # Create copy for this product
            if self._create_local_image_copy(source_image, product_id):
                result['success'] = True
                result['image_source'] = 'local_fallback'
                result['image_url'] = None  # Will use frontend fallback logic
                result['method_used'] = f'local_fallback_copy_{source_image}'
                logger.info(f"Created local image fallback for {product_id}")
                return result
        
        # Strategy 4: Use placeholder as last resort
        result['success'] = True
        result['image_source'] = 'placeholder'
        result['image_url'] = None
        result['method_used'] = 'placeholder_fallback'
        logger.warning(f"No match found for {product_id}, using placeholder")
        
        return result
    
    def batch_match_images(
        self, 
        product_ids: List[str], 
        update_database: bool = True
    ) -> Dict[str, Dict]:
        """Match images for multiple products at once.
        
        Args:
            product_ids: List of product IDs to match
            update_database: Whether to update the database with matched URLs
            
        Returns:
            Dict mapping product_id to match result
        """
        results = {}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for pid in product_ids:
            cursor.execute('SELECT name, category FROM products WHERE id = ?', (pid,))
            row = cursor.fetchone()
            
            if row:
                name, category = row
                result = self.match_image_for_product(pid, name, category)
                results[pid] = result
            else:
                results[pid] = {
                    'success': False,
                    'error': 'Product not found in database'
                }
        
        conn.close()
        return results


# Singleton instance
_matcher_service = None

def get_image_matcher() -> ImageMatcherService:
    """Get the singleton ImageMatcherService instance."""
    global _matcher_service
    if _matcher_service is None:
        _matcher_service = ImageMatcherService()
    return _matcher_service
