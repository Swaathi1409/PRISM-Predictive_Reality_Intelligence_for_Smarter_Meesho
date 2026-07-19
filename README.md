# PRISM — Predictive Reality Intelligence for Smarter Meesho

> **ScriptedBy{Her} 2.0** · Meesho Hackathon 2026  
> The first agentic AI commerce brain that understands *why* you're buying, not just *what* you want.

---

## What is PRISM?

PRISM detects the life event behind every purchase (hostel move, wedding, new baby, first job...), runs a 4-agent debate to evaluate product trustworthiness, budget fit, and delivery feasibility, then produces a confidence score decomposed into auditable factors — all wrapped in a culturally-aware message that speaks to the *human moment* of shopping in India.

### The 6 PRISM Pillars

| Pillar | What it does |
|--------|-------------|
| **Life Event Detection** | Keyword-matches 8 event templates from free text |
| **Multi-Agent Debate** | Kismat (trust) · Paisa (budget) · Samay (time) · Soch (synthesis) |
| **Confidence Genome** | Decomposes the score into per-agent, per-signal factors |
| **Temporal Simulator** | Buy Now / Wait / Split with government scheme detection |
| **Emotional Layer** | Register-switched warm opening message (Claude LLM) |
| **Bharat Context** | Institution wattage limits, state climate, PM Kisan timing |

---

## Quick Start — Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- An Anthropic API key (`sk-ant-...`)

### 1. Clone and configure

```bash
git clone https://github.com/Swaathi1409/PRISM-Predictive_Reality_Intelligence_for_Smarter_Meesho
cd PRISM-Predictive_Reality_Intelligence_for_Smarter_Meesho

# Fill in your Anthropic API key
# Open .env and set: ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Start the backend

```bash
cd backend

# Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --port 8000
```

Backend runs at **http://localhost:8000**  
Interactive API docs at **http://localhost:8000/docs**

### 3. Start the frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend runs at **http://localhost:5173**

---

## Quick Start — Docker (Production)

```bash
# 1. Fill in .env with your ANTHROPIC_API_KEY

# 2. Build the frontend (Nginx serves static files)
cd frontend && npm install && npm run build && cd ..

# 3. Start all services
docker-compose up --build

# App runs at http://localhost:80
# API docs at http://localhost:8000/docs (direct backend access)
```

---

## Testing the API

Open **http://localhost:8000/docs** and try:

**POST /api/prism/analyze**
```json
{
  "user_input": "my son just got into IIT Bombay, need hostel essentials",
  "user_pincode": "400076",
  "budget": 50000
}
```

Expected response includes: `detected_event`, `emotional_message`, `agent_debate` (4 agents), `confidence` (with factors), `temporal_strategies` (3 strategies), `bharat_context`.

**GET /api/sessions/history** — Confirms real data is being stored per request.  
**GET /api/health** — Checks DB connectivity and API key configuration.

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## Project Structure

```
prism/
├── backend/
│   ├── app/
│   │   ├── agents/          # Kismat, Paisa, Samay, Soch
│   │   ├── engines/         # Life event, emotional, confidence, temporal, product matcher
│   │   ├── services/        # PrismService — master orchestrator
│   │   ├── routes/          # FastAPI route handlers (no business logic)
│   │   ├── models/          # SQLAlchemy ORM + Pydantic schemas
│   │   ├── data/            # JSON data files (bharat_context, templates, products)
│   │   ├── utils/           # Logger, Redis cache
│   │   ├── config.py        # Single env-var reader (only place os.getenv is called)
│   │   └── main.py          # App factory
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # 14 React components
│   │   ├── pages/           # Home, Demo, About
│   │   ├── hooks/           # usePrismAnalysis, useSessionHistory
│   │   ├── utils/           # api.js, constants.js
│   │   └── context/         # PrismContext
│   └── package.json
├── nginx/nginx.conf
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Environment Variables

All configurable values are in `.env`. See `.env.example` for the full list.

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | **Required.** Your Anthropic API key | — |
| `LLM_MODEL` | Claude model to use | `claude-sonnet-4-5` |
| `DATABASE_URL` | SQLAlchemy connection string | SQLite (dev) |
| `REDIS_HOST` | Redis host for caching | `localhost` |
| `TRUST_GOOD_RATING_MIN` | Min seller rating for approval | `4.0` |
| `CONFIDENCE_BASE_SCORE` | Starting confidence before agents | `60` |

Full list in [.env.example](.env.example).

---

## Open Source Attribution

| Library | License | Why |
|---------|---------|-----|
| FastAPI | MIT | Native async, auto OpenAPI docs |
| Anthropic SDK | Anthropic Terms | Claude LLM for Soch + EmotionalLayer |
| SQLAlchemy | MIT | Database-agnostic ORM |
| Pydantic v2 | MIT | Strict API boundary validation |
| Redis-py | BSD | Result caching for demo |
| React 18 | MIT | Component-based UI |
| Framer Motion | MIT | Agent debate animations |
| TanStack React Query | MIT | Declarative loading/error states |
| Tailwind CSS | MIT | Utility-first styling |
| Docker | Apache 2.0 | Reproducible builds |

Full attribution table visible in the app at **/about**.

---

## Built by

Developed by **Swaathi B** as part of the **Meesho ScriptedBy{Her} 2.0 Hackathon**.

PRISM is built with the conviction that Indian commerce deserves AI that understands India — its institutions, its festivals, its family dynamics, its government schemes, and the emotional weight of every major purchase decision.
