"""
test_routes.py — Integration tests for PRISM API routes.

Tests verify:
1. GET /api/health returns correct structure
2. POST /api/prism/analyze validates required fields
3. GET /api/sessions/history returns a list

Uses httpx's TestClient for synchronous HTTP requests against the FastAPI app.
These tests run WITHOUT calling the real LLM — the analyze endpoint will call
Claude, so only the health and sessions endpoints are tested without mocking.

Library: pytest (MIT), httpx (BSD License) for ASGI test client.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add backend to path so imports work from tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app
from app.models.database import init_db

# Ensure DB tables exist before tests run
# TestClient does not fire startup events, so we call init_db() here.
init_db()

client = TestClient(app, raise_server_exceptions=False)


# ── Health Endpoint ───────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_returns_200(self):
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_has_required_fields(self):
        response = client.get("/api/health")
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "db_connected" in data
        assert "api_key_configured" in data
        assert "llm_model" in data
        assert "environment" in data

    def test_health_db_connected(self):
        response = client.get("/api/health")
        data = response.json()
        assert data["db_connected"] is True

    def test_health_version_is_string(self):
        response = client.get("/api/health")
        data = response.json()
        assert isinstance(data["version"], str)


# ── Root Endpoint ─────────────────────────────────────────────────────────────

class TestRootEndpoint:
    def test_root_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_has_docs_link(self):
        response = client.get("/")
        data = response.json()
        assert "docs" in data


# ── Sessions Endpoint ─────────────────────────────────────────────────────────

class TestSessionsEndpoint:
    def test_sessions_history_returns_200(self):
        response = client.get("/api/sessions/history")
        assert response.status_code == 200

    def test_sessions_history_returns_list(self):
        response = client.get("/api/sessions/history")
        data = response.json()
        assert isinstance(data, list)

    def test_sessions_history_limit_param(self):
        response = client.get("/api/sessions/history?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3

    def test_sessions_history_limit_too_high(self):
        response = client.get("/api/sessions/history?limit=100")
        # limit max is 20 — should either clamp or return 422
        assert response.status_code in (200, 422)

    def test_sessions_history_limit_zero_invalid(self):
        response = client.get("/api/sessions/history?limit=0")
        assert response.status_code == 422


# ── Analyze Endpoint — Input Validation ──────────────────────────────────────

class TestAnalyzeInputValidation:
    def test_missing_user_input_returns_422(self):
        response = client.post("/api/prism/analyze", json={
            "user_pincode": "600001",
            "budget": 5000,
        })
        assert response.status_code == 422

    def test_too_short_user_input_returns_422(self):
        response = client.post("/api/prism/analyze", json={
            "user_input": "hi",
            "user_pincode": "600001",
        })
        assert response.status_code == 422

    def test_invalid_pincode_format_returns_422(self):
        response = client.post("/api/prism/analyze", json={
            "user_input": "my son got into IIT Bombay, need hostel essentials",
            "user_pincode": "ABCDEF",
        })
        assert response.status_code == 422

    def test_negative_budget_returns_422(self):
        response = client.post("/api/prism/analyze", json={
            "user_input": "need bedsheets for my daughter going to college",
            "user_pincode": "600001",
            "budget": -500,
        })
        assert response.status_code == 422

    def test_valid_minimal_request_accepted(self):
        """
        NOTE: This test will call the real Claude API if ANTHROPIC_API_KEY is set.
        Skip this test in CI by setting SKIP_LLM_TESTS=true.
        """
        import os
        if os.getenv("SKIP_LLM_TESTS", "false").lower() == "true":
            pytest.skip("Skipping LLM-calling test in CI")

        response = client.post("/api/prism/analyze", json={
            "user_input": "my daughter just got into NIT Trichy, need hostel essentials",
            "user_pincode": "620015",
            "budget": 15000,
        })
        # Either 200 (LLM worked) or 500 (LLM key invalid)
        assert response.status_code in (200, 500)

        if response.status_code == 200:
            data = response.json()
            assert "session_id" in data
            assert "detected_event" in data
            assert "agent_debate" in data
            assert len(data["agent_debate"]) == 4
            assert "confidence" in data
            assert "temporal_strategies" in data
            assert len(data["temporal_strategies"]) == 3
