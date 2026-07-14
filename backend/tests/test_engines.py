"""
test_engines.py — Unit tests for PRISM engines.

Tests verify:
1. LifeEventEngine correctly detects events from natural language
2. Product matcher filters by event, budget, and pincode
3. ConfidenceGenome produces valid factor breakdowns
4. TemporalSimulator produces exactly 3 strategies with correct fields

Library: pytest (MIT License).
"""

import pytest
from app.engines.life_event_engine import LifeEventEngine
from app.engines.product_matcher import match_products
from app.engines.confidence_genome import ConfidenceGenome
from app.engines.temporal_simulator import generate as temporal_generate
from app.config import settings


# ── LifeEventEngine Tests ─────────────────────────────────────────────────────

class TestLifeEventEngine:
    def setup_method(self):
        self.engine = LifeEventEngine()

    def test_detects_hostel_move_from_iit(self):
        result = self.engine.detect_event("my son got into IIT Bombay")
        assert result["event_key"] == "hostel_move"

    def test_detects_hostel_move_from_nit(self):
        result = self.engine.detect_event("my daughter got into NIT Trichy, need to pack for hostel")
        assert result["event_key"] == "hostel_move"

    def test_detects_festival_prep(self):
        result = self.engine.detect_event("preparing for Diwali, need decorations")
        assert result["event_key"] == "festival_prep"

    def test_detects_wedding(self):
        result = self.engine.detect_event("getting married next month, need shaadi shopping")
        assert result["event_key"] == "wedding"

    def test_detects_new_baby(self):
        result = self.engine.detect_event("expecting our first baby in two months")
        assert result["event_key"] == "new_baby"

    def test_detects_first_job(self):
        result = self.engine.detect_event("starting my first job next week, need formal wear")
        assert result["event_key"] == "first_job"

    def test_result_has_required_keys(self):
        result = self.engine.detect_event("moving to hostel")
        required = {"event_key", "label", "timeline_days", "purchase_phases", "emotion_level", "family_significance"}
        assert required.issubset(result.keys())

    def test_purchase_phases_are_list(self):
        result = self.engine.detect_event("going to college")
        assert isinstance(result["purchase_phases"], list)
        assert len(result["purchase_phases"]) >= 1

    def test_detects_iit_bombay_institution(self):
        _, inst_data, _, _ = self.engine.detect_location("admitted to IIT Bombay this year")
        assert inst_data is not None
        assert inst_data.get("display_name") == "IIT Bombay"

    def test_detects_nit_trichy_institution(self):
        _, inst_data, _, _ = self.engine.detect_location("joining NIT Trichy for btech")
        assert inst_data is not None
        assert "Trichy" in inst_data.get("display_name", "") or "NIT" in inst_data.get("display_name", "")

    def test_detects_state_from_institution(self):
        _, _, state_key, _ = self.engine.detect_location("got into IIT Bombay")
        assert state_key == "maharashtra"

    def test_fallback_when_no_keyword(self):
        result = self.engine.detect_event("I want to buy something nice")
        # Should fall back to a valid event key, not crash
        assert "event_key" in result
        assert result["event_key"] in [
            "festival_prep", "hostel_move", "wedding", "new_baby",
            "first_job", "new_home", "government_exam", "shop_opening"
        ]

    def test_enrich_with_context_returns_same_count(self):
        event_data = self.engine.detect_event("going to hostel")
        enriched = self.engine.enrich_with_context(event_data["purchase_phases"], None, None)
        assert len(enriched) == len(event_data["purchase_phases"])


# ── Product Matcher Tests ─────────────────────────────────────────────────────

class TestProductMatcher:
    def test_returns_list(self):
        results = match_products("hostel_move", limit=3)
        assert isinstance(results, list)

    def test_respects_limit(self):
        results = match_products("hostel_move", limit=3)
        assert len(results) <= 3

    def test_filters_out_of_stock(self):
        results = match_products("hostel_move", limit=10)
        for p in results:
            assert p["stock_status"] != "out_of_stock"

    def test_budget_filter(self):
        results = match_products("new_home", budget=500, limit=10)
        for p in results:
            assert p["price"] <= 500

    def test_pincode_filter_returns_reachable_first(self):
        results = match_products("hostel_move", pincode="620015", limit=5)
        # Should not be empty even if some products don't cover this pincode
        assert len(results) >= 1

    def test_wattage_filter(self):
        institution_data = {"appliance_wattage_limit": 500}
        results = match_products("hostel_move", institution_data=institution_data, limit=10)
        for p in results:
            wattage = p.get("wattage")
            if wattage is not None:
                assert wattage <= 500

    def test_returns_products_with_required_fields(self):
        results = match_products("festival_prep", limit=2)
        for p in results:
            assert "name" in p
            assert "price" in p
            assert "seller_rating" in p
            assert "delivery_days" in p

    def test_event_fallback_when_no_match(self):
        # Unlikely event key — should fall back to all products
        results = match_products("nonexistent_event_key_xyz", limit=5)
        assert len(results) >= 1


# ── ConfidenceGenome Tests ────────────────────────────────────────────────────

class TestConfidenceGenome:
    def setup_method(self):
        self.genome = ConfidenceGenome()
        self.product = {"id": "TEST001", "price": 599, "stock_status": "in_stock"}
        self.agent_results = [
            {
                "agent_name": "Kismat", "agent_role": "Trust Agent",
                "score_contribution": 18.0, "verdict": "approve",
                "data": {"seller_rating": 4.8, "seller_return_rate": 2.0, "stock_status": "in_stock"}
            },
            {
                "agent_name": "Paisa", "agent_role": "Budget Agent",
                "score_contribution": 5.0, "verdict": "approve",
                "data": {"price": 599, "budget": 5000, "price_trend_7d": -1.5}
            },
            {
                "agent_name": "Samay", "agent_role": "Time Agent",
                "score_contribution": 9.0, "verdict": "strong_approve",
                "data": {"delivery_days": 2, "pincode_reachable": True, "urgency_days": 7}
            },
        ]
        self.soch_result = {"final_score": 84.0, "verdict": "RECOMMEND", "message": "Test synthesis."}

    def test_output_has_required_keys(self):
        result = self.genome.compute(self.agent_results, self.soch_result, self.product, "600001")
        assert "total_score" in result
        assert "base_score" in result
        assert "factors" in result
        assert "interpretation" in result

    def test_total_score_within_bounds(self):
        result = self.genome.compute(self.agent_results, self.soch_result, self.product, "600001")
        assert settings.confidence_min <= result["total_score"] <= settings.confidence_max

    def test_factors_is_non_empty_list(self):
        result = self.genome.compute(self.agent_results, self.soch_result, self.product, "600001")
        assert isinstance(result["factors"], list)
        assert len(result["factors"]) > 0

    def test_factor_has_required_fields(self):
        result = self.genome.compute(self.agent_results, self.soch_result, self.product, "600001")
        for factor in result["factors"]:
            assert "factor_label" in factor
            assert "contribution" in factor
            assert "direction" in factor
            assert "agent_name" in factor
            assert factor["direction"] in {"up", "down"}

    def test_interpretation_is_string(self):
        result = self.genome.compute(self.agent_results, self.soch_result, self.product, "600001")
        assert isinstance(result["interpretation"], str) and len(result["interpretation"]) > 0


# ── TemporalSimulator Tests ───────────────────────────────────────────────────

class TestTemporalSimulator:
    def setup_method(self):
        self.product = {
            "name": "Test Product", "price": 1000,
            "delivery_days": 3, "price_trend_7d": 0.0,
        }
        self.context = {
            "urgency_days": 30, "budget": 5000,
            "detected_event": "hostel_move",
        }

    def test_returns_exactly_3_strategies(self):
        strategies = temporal_generate(self.product, self.context)
        assert len(strategies) == 3

    def test_strategy_keys_present(self):
        strategies = temporal_generate(self.product, self.context)
        required = {"strategy_name", "strategy_key", "price", "savings_vs_now", "recommended", "note", "action_date"}
        for s in strategies:
            assert required.issubset(s.keys())

    def test_exactly_one_recommended(self):
        strategies = temporal_generate(self.product, self.context)
        recommended = [s for s in strategies if s["recommended"]]
        assert len(recommended) == 1

    def test_buy_now_price_equals_base(self):
        strategies = temporal_generate(self.product, self.context)
        buy_now = next(s for s in strategies if s["strategy_key"] == "buy_now")
        assert buy_now["price"] == self.product["price"]

    def test_wait_price_is_discounted(self):
        strategies = temporal_generate(self.product, self.context)
        wait = next(s for s in strategies if s["strategy_key"] == "wait")
        expected = int(self.product["price"] * settings.temporal_sale_discount)
        assert wait["price"] == expected

    def test_urgent_context_recommends_buy_now(self):
        urgent_context = {**self.context, "urgency_days": 2}
        strategies = temporal_generate(self.product, urgent_context)
        buy_now = next(s for s in strategies if s["strategy_key"] == "buy_now")
        assert buy_now["recommended"] is True

    def test_buy_now_savings_is_zero(self):
        strategies = temporal_generate(self.product, self.context)
        buy_now = next(s for s in strategies if s["strategy_key"] == "buy_now")
        assert buy_now["savings_vs_now"] == 0
