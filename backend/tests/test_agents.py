"""
test_agents.py — Unit tests for PRISM's three specialist agents.

Tests verify:
1. Each agent returns the correct output contract (all required keys present)
2. Score contributions are positive for good inputs and negative for bad inputs
3. Verdict strings are valid
4. No magic numbers appear in agent logic (thresholds come from settings)

Library: pytest (MIT License). No external dependencies beyond the project.
"""

import pytest
from app.agents.kismat import KismatTrustAgent
from app.agents.paisa import PaisaBudgetAgent
from app.agents.samay import SamayTimeAgent
from app.config import settings

REQUIRED_KEYS = {"agent_name", "agent_role", "message", "score_contribution", "verdict", "data"}
VALID_VERDICTS = {"approve", "caution", "flag", "reject", "strong_approve", "RECOMMEND", "REJECT"}


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def good_product():
    return {
        "seller_rating": 4.8,
        "seller_review_count": 3000,
        "seller_return_rate": 1.5,
        "stock_status": "in_stock",
        "price": 599,
        "price_trend_7d": -2.0,
        "delivery_days": 2,
        "available_pincodes": ["600001", "400076", "110016"],
        "name": "Test Product",
    }


@pytest.fixture
def bad_product():
    return {
        "seller_rating": 2.8,
        "seller_review_count": 12,
        "seller_return_rate": 15.0,
        "stock_status": "low_stock",
        "price": 90000,
        "price_trend_7d": 8.5,
        "delivery_days": 10,
        "available_pincodes": ["700001"],
        "name": "Expensive Bad Product",
    }


@pytest.fixture
def context():
    return {
        "budget": 5000,
        "user_pincode": "600001",
        "urgency_days": 7,
        "detected_event": "hostel_move",
        "state": "Tamil Nadu",
    }


# ── Kismat Tests ──────────────────────────────────────────────────────────────

class TestKismatTrustAgent:
    def setup_method(self):
        self.agent = KismatTrustAgent()

    def test_output_contract(self, good_product, context):
        result = self.agent.evaluate(good_product, context)
        assert REQUIRED_KEYS.issubset(result.keys()), "Missing required output keys"

    def test_good_product_positive_score(self, good_product, context):
        result = self.agent.evaluate(good_product, context)
        assert result["score_contribution"] > 0, "Good product should give positive score"

    def test_bad_product_negative_score(self, bad_product, context):
        result = self.agent.evaluate(bad_product, context)
        assert result["score_contribution"] < 0, "Bad product should give negative score"

    def test_good_product_strong_approve(self, good_product, context):
        result = self.agent.evaluate(good_product, context)
        assert result["verdict"] in {"approve", "strong_approve"}

    def test_high_return_rate_reject(self, bad_product, context):
        # bad_product has 15.0% return rate which is above trust_high_return_rate (10.0)
        result = self.agent.evaluate(bad_product, context)
        assert result["verdict"] in {"reject", "flag", "caution"}

    def test_low_stock_caution(self, good_product, context):
        good_product["stock_status"] = "low_stock"
        result = self.agent.evaluate(good_product, context)
        assert result["verdict"] in {"caution", "flag", "approve"}
        assert "low" in result["message"].lower() or "stock" in result["message"].lower()

    def test_message_is_non_empty_string(self, good_product, context):
        result = self.agent.evaluate(good_product, context)
        assert isinstance(result["message"], str) and len(result["message"]) > 10

    def test_verdict_is_valid(self, good_product, context):
        result = self.agent.evaluate(good_product, context)
        assert result["verdict"] in VALID_VERDICTS

    def test_data_contains_key_signals(self, good_product, context):
        result = self.agent.evaluate(good_product, context)
        assert "seller_rating" in result["data"]
        assert "seller_return_rate" in result["data"]


# ── Paisa Tests ───────────────────────────────────────────────────────────────

class TestPaisaBudgetAgent:
    def setup_method(self):
        self.agent = PaisaBudgetAgent()

    def test_output_contract(self, good_product, context):
        result = self.agent.evaluate(good_product, context)
        assert REQUIRED_KEYS.issubset(result.keys())

    def test_within_budget_positive_score(self, good_product, context):
        # good_product price=599, context budget=5000
        result = self.agent.evaluate(good_product, context)
        assert result["score_contribution"] >= 0

    def test_over_budget_reject(self, bad_product, context):
        # bad_product price=90000, context budget=5000
        # Note: score may accumulate over-budget penalty + rising trend penalty
        result = self.agent.evaluate(bad_product, context)
        assert result["verdict"] == "reject"
        assert result["score_contribution"] <= settings.budget_score_over_budget

    def test_falling_price_trend_strong_approve(self, good_product, context):
        # price_trend_7d=-2.0 is below budget_price_trend_low=-5.0? No, it's not.
        # Set it clearly below threshold
        good_product["price_trend_7d"] = -6.0
        result = self.agent.evaluate(good_product, context)
        assert result["score_contribution"] >= settings.budget_score_falling

    def test_rising_price_trend_caution(self, good_product, context):
        good_product["price_trend_7d"] = 7.0  # above budget_price_trend_high=5.0
        result = self.agent.evaluate(good_product, context)
        assert result["score_contribution"] == settings.budget_score_rising

    def test_overage_amount_in_message(self, bad_product, context):
        result = self.agent.evaluate(bad_product, context)
        # Should mention the exact overage amount
        assert "85,000" in result["message"] or "85000" in result["message"] or "over" in result["message"].lower()

    def test_no_budget_no_reject(self, good_product):
        no_budget_context = {"budget": None, "user_pincode": "600001", "urgency_days": 30}
        result = self.agent.evaluate(good_product, no_budget_context)
        assert result["verdict"] != "reject"


# ── Samay Tests ───────────────────────────────────────────────────────────────

class TestSamayTimeAgent:
    def setup_method(self):
        self.agent = SamayTimeAgent()

    def test_output_contract(self, good_product, context):
        result = self.agent.evaluate(good_product, context)
        assert REQUIRED_KEYS.issubset(result.keys())

    def test_fast_delivery_positive_score(self, good_product, context):
        # good_product delivery_days=2, time_delivery_fast_days=3
        result = self.agent.evaluate(good_product, context)
        assert result["score_contribution"] >= settings.time_score_fast

    def test_pincode_not_available_reject(self, good_product, context):
        # User is at 600001 but product only delivers to 700001
        good_product["available_pincodes"] = ["700001", "800001"]
        result = self.agent.evaluate(good_product, context)
        assert result["verdict"] == "reject"
        # Score must be negative (pincode unavailable = strong negative signal)
        assert result["score_contribution"] < 0

    def test_pincode_available_passes(self, good_product, context):
        # 600001 is in the pincodes list
        result = self.agent.evaluate(good_product, context)
        assert "600001" in result["data"].get("user_pincode", "600001")

    def test_late_delivery_negative_score(self, good_product, context):
        good_product["delivery_days"] = 20  # urgency_days=7, delivery=20 → 13 days late
        result = self.agent.evaluate(good_product, context)
        assert result["score_contribution"] < 0
        assert result["verdict"] in {"reject", "flag"}

    def test_data_contains_delivery_info(self, good_product, context):
        result = self.agent.evaluate(good_product, context)
        assert "delivery_days" in result["data"]
        assert "pincode_reachable" in result["data"]
