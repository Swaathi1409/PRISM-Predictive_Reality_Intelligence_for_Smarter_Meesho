"""
image_matcher.py — API endpoint for on-demand image matching.

POST /api/images/match - Match images for products on-demand
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.services.image_matcher_service import get_image_matcher
from app.utils.logger import get_logger

router = APIRouter(tags=["images"])
logger = get_logger(__name__)


class ImageMatchRequest(BaseModel):
    """Request model for image matching."""
    product_ids: List[str]
    update_database: bool = True


class ImageMatchResponse(BaseModel):
    """Response model for image matching."""
    success: bool
    results: dict
    total_matched: int
    total_failed: int


@router.post("/match", response_model=ImageMatchResponse)
async def match_images(request: ImageMatchRequest):
    """
    Match images for multiple products on-demand.
    
    This endpoint automatically:
    1. Finds similar products with Amazon URLs
    2. Creates local image fallbacks by copying similar images
    3. Updates the database with matched URLs
    4. Returns detailed results for each product
    
    **Example:**
    ```json
    {
      "product_ids": ["PROD001", "PROD002"],
      "update_database": true
    }
    ```
    """
    logger.info(f"Image matching request for {len(request.product_ids)} products")
    
    try:
        matcher = get_image_matcher()
        results = matcher.batch_match_images(
            request.product_ids, 
            update_database=request.update_database
        )
        
        # Calculate statistics
        total_matched = sum(1 for r in results.values() if r.get('success', False))
        total_failed = len(results) - total_matched
        
        return ImageMatchResponse(
            success=True,
            results=results,
            total_matched=total_matched,
            total_failed=total_failed
        )
        
    except Exception as e:
        logger.error(f"Image matching failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Image matching failed: {str(e)}"
        )


@router.get("/match/{product_id}")
async def match_single_image(product_id: str):
    """
    Match image for a single product.
    
    **Example:**
    GET /api/images/match/PROD001
    """
    logger.info(f"Single image matching request for {product_id}")
    
    try:
        matcher = get_image_matcher()
        
        # Get product details from database
        import sqlite3
        conn = sqlite3.connect(matcher.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT name, category FROM products WHERE id = ?', (product_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Product {product_id} not found"
            )
        
        name, category = row
        result = matcher.match_image_for_product(product_id, name, category)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Single image matching failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Image matching failed: {str(e)}"
        )


@router.get("/stats")
async def get_image_stats():
    """
    Get statistics about image coverage in the database.
    
    Returns:
    - Total products
    - Products with Amazon URLs
    - Products with local images
    - Products without images
    """
    try:
        import sqlite3
        import os
        
        matcher = get_image_matcher()
        conn = sqlite3.connect(matcher.db_path)
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
        
        # Local images count
        local_images = len(matcher._get_local_images())
        
        conn.close()
        
        return {
            "total_products": total,
            "with_amazon_urls": amazon_count,
            "without_images": no_image_count,
            "local_images_available": local_images,
            "image_coverage_percentage": round(((total - no_image_count) / total) * 100, 2) if total > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Failed to get image stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )
