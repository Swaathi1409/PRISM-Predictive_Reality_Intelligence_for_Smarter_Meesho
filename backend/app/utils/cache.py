"""
cache.py — Redis cache helper for PRISM.

WHY Redis (BSD License):
Caches analysis results keyed by input hash so that repeated demo queries
return instantly without re-calling the LLM. Critical for a live demo where
judges may re-run the same inputs. Falls back gracefully if Redis is unavailable
(e.g. local dev without Redis running) — the system continues to work, just slower.

Library: redis-py (BSD License). Chosen for simple, synchronous Redis client with
connection pooling and graceful error handling.
"""

import hashlib
import json
from typing import Any, Optional

import redis

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Try to connect at import time; set REDIS_AVAILABLE = False if Redis is down
try:
    _client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=True,
        socket_connect_timeout=2,
    )
    _client.ping()
    REDIS_AVAILABLE = True
    logger.info(f"Redis connected at {settings.redis_host}:{settings.redis_port}")
except Exception as e:
    REDIS_AVAILABLE = False
    _client = None
    logger.warning(f"Redis unavailable ({e}). Cache disabled — system will still work.")


def cache_key(user_input: str, pincode: str, budget: str, target_date: str = "") -> str:
    """Generates a deterministic cache key from the analysis inputs."""
    raw = f"{user_input.lower().strip()}|{pincode}|{budget}|{target_date}"
    return f"prism:v2:{hashlib.md5(raw.encode()).hexdigest()}"


def get_cached(key: str) -> Optional[Any]:
    """Returns the cached value for key, or None if not found or Redis is down."""
    if not REDIS_AVAILABLE or _client is None:
        return None
    try:
        val = _client.get(key)
        return json.loads(val) if val else None
    except Exception as e:
        logger.warning(f"Cache read failed: {e}")
        return None


def set_cached(key: str, value: dict) -> None:
    """Stores value in Redis with the configured TTL. Silent fail if Redis is down."""
    if not REDIS_AVAILABLE or _client is None:
        return
    try:
        _client.setex(key, settings.redis_ttl_seconds, json.dumps(value, default=str))
    except Exception as e:
        logger.warning(f"Cache write failed: {e}")
