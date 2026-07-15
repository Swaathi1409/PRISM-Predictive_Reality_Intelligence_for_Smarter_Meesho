"""
schemas.py — Pydantic v2 request and response models for PRISM API.

WHY Pydantic (MIT License):
Enforces strict type checking on all API inputs and outputs at the boundary layer.
Every field has a description string so that the auto-generated OpenAPI docs at
/docs are self-explanatory — judges can understand and test the API without
reading the source code.

All fields are required unless explicitly typed as Optional with a default.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ─────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────

class PrismRequest(BaseModel):
    user_input: str = Field(
        ...,
        description="Natural language description of the user's purchase context. E.g. 'my son just got into IIT Bombay, need to buy hostel essentials'",
        min_length=5,
        max_length=500,
    )
    user_pincode: str = Field(
        default="600001",
        description="User's delivery pincode. Used for product availability check and delivery time estimate.",
        pattern=r"^\d{6}$",
    )
    budget: Optional[int] = Field(
        default=None,
        description="User's maximum budget in Indian Rupees. If provided, products above this price are filtered out.",
        ge=0,
        le=10000000,
    )
    state_hint: Optional[str] = Field(
        default=None,
        description="Optional state name hint if the user's state is known from their profile. E.g. 'tamil_nadu'.",
    )
    target_date: Optional[str] = Field(
        default=None,
        description="Optional target date for the event. E.g. '2026-08-15'.",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )


# ─────────────────────────────────────────────
# AGENT RESPONSE MODELS
# ─────────────────────────────────────────────

class AgentMessage(BaseModel):
    agent_name: str = Field(..., description="Name of the agent (Kismat, Paisa, Samay, or Soch).")
    agent_role: str = Field(..., description="Role label of the agent (e.g. 'Trust Agent').")
    message: str = Field(..., description="Human-readable explanation of this agent's verdict.")
    score_contribution: float = Field(..., description="Score this agent adds or subtracts from base confidence. Positive = good signal, negative = risk signal.")
    verdict: str = Field(..., description="One of: approve, caution, flag, reject, strong_approve, RECOMMEND, REJECT.")
    data: dict = Field(default={}, description="Raw signals this agent used to reach its verdict.")


# ─────────────────────────────────────────────
# CONFIDENCE GENOME
# ─────────────────────────────────────────────

class ConfidenceFactor(BaseModel):
    factor_label: str = Field(..., description="Human-readable label for this confidence factor. E.g. 'Seller Rating'.")
    contribution: float = Field(..., description="How much this factor contributes to the confidence score (positive or negative).")
    direction: str = Field(..., description="'up' if this factor boosts confidence, 'down' if it reduces it.")
    agent_name: str = Field(..., description="Which agent produced this factor.")


class ConfidenceBreakdown(BaseModel):
    total_score: float = Field(..., description="Final confidence score from 10 to 98.")
    base_score: int = Field(..., description="Starting base score before agent contributions.")
    factors: List[ConfidenceFactor] = Field(..., description="List of all factors that contributed to the final score, in order of magnitude.")
    interpretation: str = Field(..., description="Plain-language interpretation of the confidence score. E.g. 'High confidence — buy with assurance.'")


# ─────────────────────────────────────────────
# TEMPORAL SIMULATOR
# ─────────────────────────────────────────────

class TemporalStrategy(BaseModel):
    strategy_name: str = Field(..., description="Name of the strategy: 'Buy Now', 'Wait for Sale', or 'Split Purchase'.")
    strategy_key: str = Field(..., description="Machine-readable key: buy_now, wait, split.")
    price: int = Field(..., description="Expected price in INR under this strategy.")
    savings_vs_now: int = Field(default=0, description="INR saved compared to buying now. 0 for Buy Now strategy.")
    recommended: bool = Field(..., description="True for the strategy PRISM recommends based on the user's context.")
    note: str = Field(..., description="1-2 sentence explanation of why this strategy is or isn't recommended.")
    action_date: str = Field(..., description="Human-readable date or timeframe for acting on this strategy. E.g. 'Order today by 3 PM' or 'Wait until next Diwali sale (23 Oct)'.")


# ─────────────────────────────────────────────
# LIFE EVENT & PURCHASE TIMELINE
# ─────────────────────────────────────────────

class PurchasePhase(BaseModel):
    phase_name: str = Field(..., description="Name of this purchase phase. E.g. 'Essential Setup (Week 1)'.")
    days_from_now: int = Field(..., description="Days from today to act on this phase.")
    categories: List[str] = Field(..., description="Product categories to buy in this phase.")
    priority: str = Field(..., description="One of: must_have, should_have, nice_to_have.")
    note: str = Field(..., description="Contextual note for this phase specific to the user's situation.")


# ─────────────────────────────────────────────
# BHARAT CONTEXT
# ─────────────────────────────────────────────

class BharatContextDisplay(BaseModel):
    institution_name: Optional[str] = Field(default=None, description="Name of the detected institution, if any.")
    institution_type: Optional[str] = Field(default=None, description="Type of institution: iit, nit, deemed_university.")
    state_name: Optional[str] = Field(default=None, description="Display name of the detected state.")
    wattage_limit: Optional[int] = Field(default=None, description="Appliance wattage limit imposed by the institution.")
    relevant_festivals: Optional[List[str]] = Field(default=None, description="Upcoming festivals in the user's state relevant to purchase timing.")
    government_scheme_note: Optional[str] = Field(default=None, description="Note about any relevant government scheme payment due soon.")
    climate_note: Optional[str] = Field(default=None, description="Brief climate-relevant note for product selection.")
    contextual_notes: Optional[List[str]] = Field(default=None, description="Additional contextual notes derived from state and institution data.")


# ─────────────────────────────────────────────
# MAIN RESPONSE
# ─────────────────────────────────────────────

class PrismResponse(BaseModel):
    session_id: str = Field(..., description="Unique session ID for this analysis. Use to retrieve history via /api/sessions/history.")
    detected_event: str = Field(..., description="Human-readable label of the detected life event.")
    event_key: str = Field(..., description="Machine-readable event key. E.g. 'hostel_move'.")
    emotion_level: str = Field(..., description="Detected emotion level: high, very_high, moderate.")
    family_significance: str = Field(..., description="Family significance of the event: high, very_high, extremely_high.")
    emotional_message: str = Field(..., description="Warm, personalised opening message generated by the emotional layer.")
    purchase_timeline: List[PurchasePhase] = Field(..., description="Phased purchase plan for the detected event.")
    agent_debate: List[AgentMessage] = Field(..., description="Messages from all 4 agents (Kismat, Paisa, Samay, Soch) with their verdicts.")
    top_recommendation: dict = Field(..., description="The top recommended product with all its details.")
    all_products: List[dict] = Field(default=[], description="List of all products considered, useful for mapping to purchase phases.")
    confidence: ConfidenceBreakdown = Field(..., description="Decomposed confidence score with per-factor breakdown.")
    temporal_strategies: List[TemporalStrategy] = Field(..., description="Three purchase timing strategies: Buy Now, Wait for Sale, Split Purchase.")
    bharat_context: BharatContextDisplay = Field(..., description="Cultural and institutional context detected from the user's input.")
    state_detected: Optional[str] = Field(default=None, description="Machine-readable state key detected from the input.")
    institution_detected: Optional[str] = Field(default=None, description="Machine-readable institution key detected from the input.")
    llm_roadmap: Optional[str] = Field(default=None, description="LLM-generated personalised 2-sentence purchase plan intro.")


# ─────────────────────────────────────────────
# SESSION HISTORY
# ─────────────────────────────────────────────

class SessionSummary(BaseModel):
    session_id: str = Field(..., description="Unique session ID.")
    user_input: str = Field(..., description="The original user input (truncated to 100 chars).")
    detected_event: str = Field(..., description="Detected life event label.")
    event_key: str = Field(..., description="Machine-readable event key.")
    state_detected: Optional[str] = Field(default=None, description="Detected state key.")
    institution_detected: Optional[str] = Field(default=None, description="Detected institution key.")
    created_at: Optional[datetime] = Field(default=None, description="When this session was created.")


# ─────────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = Field(..., description="'healthy' if all systems are operational, 'degraded' if any check fails.")
    version: str = Field(..., description="API version.")
    environment: str = Field(..., description="Current environment: development or production.")
    db_connected: bool = Field(..., description="True if database connection is working.")
    api_key_configured: bool = Field(..., description="True if GROQ_API_KEY is set and non-empty.")
    llm_model: str = Field(..., description="The LLM model currently configured.")
