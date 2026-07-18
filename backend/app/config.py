"""
config.py — Central configuration for PRISM backend.

WHY THIS FILE EXISTS:
All environment variables are read exactly once, here, at startup.
Every other module imports from this file rather than calling os.getenv directly.
This means: one place to audit all config, one place to add defaults, one place
to see what the application needs to run.

Libraries used: pydantic-settings (MIT License) for typed env var parsing with
validation. Chosen over plain os.getenv because it gives type coercion, default
values, and validation errors at startup rather than at runtime.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Core
    groq_api_key: str = "not_set"
    environment: str = "development"
    log_level: str = "INFO"
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"

    # LLM
    llm_model: str = "llama-3.1-8b-instant"
    llm_max_tokens_orchestrator: int = 250
    llm_max_tokens_emotional: int = 180
    llm_max_tokens_event: int = 150
    llm_temperature: float = 0.3

    # Database
    database_url: str = "sqlite:///./prism_dev.db"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_ttl_seconds: int = 3600

    # Agent Score Thresholds — Trust (Kismat)
    trust_good_rating_min: float = 4.0
    trust_high_return_rate: float = 10.0
    trust_medium_return_rate: float = 5.0
    trust_score_good: int = 18
    trust_score_medium: int = -7
    trust_score_bad: int = -15

    # Agent Score Thresholds — Budget (Paisa)
    budget_price_trend_high: float = 5.0
    budget_price_trend_low: float = -5.0
    budget_score_stable: int = 5
    budget_score_rising: int = -7
    budget_score_falling: int = 10
    budget_score_over_budget: int = -20

    # Agent Score Thresholds — Time (Samay)
    time_delivery_fast_days: int = 3
    time_score_fast: int = 9
    time_score_normal: int = 4
    time_score_late: int = -12
    time_score_unreachable: int = -25

    # Confidence Genome
    confidence_base_score: int = 60
    confidence_pincode_match_boost: int = 12
    confidence_max: int = 98
    confidence_min: int = 10

    # Temporal Simulator
    temporal_sale_discount: float = 0.80
    temporal_split_fraction: float = 0.55
    temporal_wait_days: int = 6

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
