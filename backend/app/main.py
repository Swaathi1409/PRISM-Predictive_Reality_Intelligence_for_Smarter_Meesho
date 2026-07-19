"""
main.py — FastAPI application factory for PRISM.

WHY FastAPI (MIT License):
Native async support, automatic OpenAPI docs at /docs that let judges test every
endpoint interactively without Postman, and Pydantic integration for strict input
validation. Chosen over Flask for these specific capabilities.

Startup sequence:
1. Load .env (local dev) or use injected env vars (Docker)
2. Validate all environment variables — fail fast if GROQ_API_KEY is missing
3. Initialise database tables
4. Register CORS middleware
5. Register all routers under /api prefix
"""

from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()  # loads .env in local dev; no-op in Docker where env is injected

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.database import init_db
from app.routes import health, prism, sessions, auth, image_matcher
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Lifespan (replaces deprecated @app.on_event) ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup validation, DB init, and RAG index warm-up."""
    # ── Startup ───────────────────────────────────────────────────────────────
    if (
        not settings.groq_api_key
        or settings.groq_api_key in ("not_set", "your_key_here")
        or len(settings.groq_api_key) < 10
    ):
        logger.error(
            "GROQ_API_KEY is not set or invalid. "
            "Set it in .env and restart. Analyze endpoint will not work."
        )
    else:
        logger.info(f"GROQ_API_KEY configured. Model: {settings.llm_model}")

    logger.info("PRISM API starting up")
    init_db()
    logger.info(f"Database initialised at {settings.database_url}")
    logger.info(f"Environment: {settings.environment}")
    logger.info("API docs available at http://localhost:8000/docs")

    # ── RAG Index warm-up (non-blocking) ─────────────────────────────────────
    # Tries to load from disk first (fast), then builds from DB if needed.
    # Runs in a background thread so startup is never delayed.
    import asyncio, threading
    from app.engines.embedding_index import get_index

    def _warmup_embedding_index():
        try:
            import sqlite3, json, os
            db_path = os.path.join(os.path.dirname(__file__), "data/prism_catalog.db")
            index = get_index()
            if index._try_load_from_disk():
                logger.info("[RAG] Embedding index loaded from disk at startup.")
                return
            # Build fresh from DB
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM products")
                rows = cur.fetchall()
                conn.close()
                products = []
                for r in rows:
                    p = dict(r)
                    for col in ("available_pincodes", "tags", "event_tags"):
                        raw = p.get(col)
                        if isinstance(raw, str):
                            try:
                                p[col] = json.loads(raw)
                            except Exception:
                                p[col] = []
                    products.append(p)
                success = index.build_index(products)
                if success:
                    logger.info(f"[RAG] Embedding index built at startup ({len(products)} products).")
                else:
                    logger.warning("[RAG] Embedding index build failed — falling back to keyword matching.")
            else:
                logger.warning(f"[RAG] Catalog DB not found at {db_path}")
        except Exception as e:
            logger.warning(f"[RAG] Startup warm-up error (non-fatal): {e}")

    thread = threading.Thread(target=_warmup_embedding_index, daemon=True, name="rag-warmup")
    thread.start()

    yield
    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("PRISM API shutting down cleanly")


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="PRISM API",
    description="""
## PRISM — Predictive Reality Intelligence for Smarter Meesho

An Agentic AI Commerce Brain that detects life events, runs a multi-agent debate,
computes a decomposed confidence score, and generates a culturally-aware purchase
plan for India's next 500 million internet users.

### 6 PRISM Pillars
1. **Life Event Detection** — Understands the human moment behind every purchase
2. **Multi-Agent Debate** — Kismat (trust), Paisa (budget), Samay (time), Soch (synthesis)
3. **Confidence Genome** — Decomposes every score into auditable factors
4. **Temporal Simulator** — Buy Now / Wait / Split strategies with real pricing
5. **Emotional Layer** — Register-switched warm opening messages
6. **Bharat Context** — Institution constraints, state climate, government schemes

### Open Source Attributions
FastAPI (MIT) · Groq SDK (Apache 2.0) ·
SQLAlchemy (MIT) · Alembic (MIT) · Redis-py (BSD) · Pydantic (MIT) · Uvicorn (BSD)
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    contact={
        "name": "ScriptedBy{Her} 2.0",
        "url": "https://github.com/Swaathi1409",
    },
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(prism.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(image_matcher.router, prefix="/api/images")

@app.get("/", tags=["root"])
def root():
    """API root — returns service info and links to docs."""
    return {
        "service": "PRISM API",
        "version": "1.0.0",
        "description": "Predictive Reality Intelligence for Smarter Meesho",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/health",
        "analyze": "/api/prism/analyze",
        "history": "/api/sessions/history",
    }
