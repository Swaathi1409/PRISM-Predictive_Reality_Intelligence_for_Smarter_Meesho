"""
groq_client.py — Centralised, resilient Groq client for PRISM.

WHY THIS EXISTS:
Groq's free tier enforces rate limits: ~30 req/min on llama-3.3-70b-versatile.
When a judge runs 5–10 test cases back-to-back, the 5 LLM calls per request
(event detection + LLM roadmap + soch + emotional layer + product filter) can
easily hit the rate-limit wall, returning HTTP 429 errors that crash the endpoint.

THIS MODULE PROVIDES:
1. A singleton Groq client (no repeated init overhead).
2. `groq_chat()` — a drop-in wrapper for `client.chat.completions.create()`
   with automatic exponential backoff retry on 429 and transient 5xx errors.
3. Model fallback cascade: if the primary model is rate-limited, falls back to
   a smaller/faster model that has a separate rate-limit bucket.
4. Jitter to prevent thundering-herd when multiple workers retry simultaneously.

USAGE (replace all direct _client.chat.completions.create() calls):
    from app.utils.groq_client import groq_chat
    response = groq_chat(model="llama-3.3-70b-versatile", messages=[...], ...)

All keyword arguments are forwarded as-is to the Groq SDK.

Libraries: groq (Apache 2.0), time (stdlib), random (stdlib), logging (stdlib).
"""

import logging
import random
import time
from typing import Any, Dict, List, Optional

from groq import Groq, RateLimitError, APIStatusError, APITimeoutError, APIConnectionError

from app.config import settings

logger = logging.getLogger(__name__)

# ── Singleton Groq client ─────────────────────────────────────────────────────
_client: Optional[Groq] = None


def get_client() -> Groq:
    """Returns the module-level singleton Groq client."""
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


# ── Model fallback cascade ────────────────────────────────────────────────────
# Each tier is tried in order when the current one is rate-limited.
# Tier 0 = best quality; Tier 1+ = faster/lighter fallbacks.
_MODEL_FALLBACK_CHAIN: Dict[str, List[str]] = {
    # Primary orchestration model (70b) falls back to 8b variants
    "llama-3.3-70b-versatile": [
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-8b-8192",
    ],
    # 8b models fall back to gemma if available
    "llama-3.1-8b-instant": [
        "llama3-8b-8192",
        "gemma2-9b-it",
    ],
    # Other known models
    "llama3-70b-8192": [
        "llama-3.1-8b-instant",
        "llama3-8b-8192",
    ],
    "gemma2-9b-it": [
        "llama-3.1-8b-instant",
    ],
}

# ── Retry configuration ───────────────────────────────────────────────────────
_MAX_RETRIES = 4          # Total attempts (1 original + 3 retries)
_BASE_DELAY_S = 2.0       # Initial backoff seconds
_MAX_DELAY_S = 30.0       # Cap so we never wait more than 30s
_JITTER_RANGE = 0.5       # ±0.5s random jitter to spread retries


def _with_jitter(delay: float) -> float:
    return delay + random.uniform(-_JITTER_RANGE, _JITTER_RANGE)


def groq_chat(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 1200,
    timeout: float = 30.0,
    response_format: Optional[Dict] = None,
    **kwargs,
) -> Any:
    """
    Drop-in replacement for `client.chat.completions.create()` with:
    - Automatic exponential backoff retry on 429 (rate limit)
    - Automatic retry on transient 5xx / timeout errors
    - Model fallback cascade when rate limits are persistent

    Returns the Groq API response object on success.
    Raises the last exception if all retries are exhausted.
    """
    client = get_client()
    fallback_models = _MODEL_FALLBACK_CHAIN.get(model, [])
    model_chain = [model] + fallback_models

    last_exc = None

    for model_attempt, current_model in enumerate(model_chain):
        delay = _BASE_DELAY_S
        for attempt in range(_MAX_RETRIES):
            try:
                call_kwargs = dict(
                    model=current_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                    **kwargs,
                )
                if response_format is not None:
                    call_kwargs["response_format"] = response_format

                response = client.chat.completions.create(**call_kwargs)
                if model_attempt > 0 or attempt > 0:
                    logger.info(
                        f"[GroqClient] Success after fallback "
                        f"(model={current_model}, attempt={attempt + 1})"
                    )
                return response

            except RateLimitError as e:
                last_exc = e
                # Check if Groq returned a Retry-After header
                retry_after = None
                try:
                    retry_after = float(e.response.headers.get("retry-after", 0))
                except Exception:
                    pass

                wait = max(retry_after or 0, _with_jitter(delay))
                wait = min(wait, _MAX_DELAY_S)

                logger.warning(
                    f"[GroqClient] 429 Rate Limit on {current_model} "
                    f"(attempt {attempt + 1}/{_MAX_RETRIES}). "
                    f"Waiting {wait:.1f}s..."
                )
                time.sleep(wait)
                delay = min(delay * 2, _MAX_DELAY_S)  # Exponential backoff

            except APITimeoutError as e:
                last_exc = e
                wait = _with_jitter(delay)
                logger.warning(
                    f"[GroqClient] Timeout on {current_model} "
                    f"(attempt {attempt + 1}/{_MAX_RETRIES}). "
                    f"Retrying in {wait:.1f}s..."
                )
                time.sleep(wait)
                delay = min(delay * 1.5, _MAX_DELAY_S)

            except APIConnectionError as e:
                last_exc = e
                wait = _with_jitter(delay)
                logger.warning(
                    f"[GroqClient] Connection error on {current_model} "
                    f"(attempt {attempt + 1}/{_MAX_RETRIES}). "
                    f"Retrying in {wait:.1f}s..."
                )
                time.sleep(wait)
                delay = min(delay * 1.5, _MAX_DELAY_S)

            except APIStatusError as e:
                last_exc = e
                # Only retry on 5xx server errors; propagate 4xx client errors immediately
                if e.status_code and 500 <= e.status_code < 600:
                    wait = _with_jitter(delay)
                    logger.warning(
                        f"[GroqClient] {e.status_code} Server Error on {current_model} "
                        f"(attempt {attempt + 1}/{_MAX_RETRIES}). "
                        f"Retrying in {wait:.1f}s..."
                    )
                    time.sleep(wait)
                    delay = min(delay * 1.5, _MAX_DELAY_S)
                else:
                    # 4xx error (not rate limit) — don't retry, re-raise immediately
                    raise

            except Exception as e:
                # Unknown error — propagate immediately
                raise

        # Exhausted all retries for this model — try next in fallback chain
        logger.warning(
            f"[GroqClient] Exhausted retries on model={current_model}. "
            f"Trying next fallback..."
        )

    # All models exhausted
    logger.error(
        f"[GroqClient] All models exhausted. Last error: {last_exc}"
    )
    raise last_exc
