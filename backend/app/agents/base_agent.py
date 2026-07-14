"""
base_agent.py — Abstract base class for all PRISM agents.

WHY THIS EXISTS:
All four agents (Kismat, Paisa, Samay, Soch) share the same output contract.
By defining an abstract base, we guarantee every agent returns the same dict
structure, which the orchestrator and confidence genome can rely on without
defensive checks. This is the core of the modular architecture.

Library: abc (stdlib, no license needed).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseAgent(ABC):
    name: str
    role: str
    personality: str

    @abstractmethod
    def evaluate(self, product: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a product given context. Must return a dict with exactly:
        - agent_name: str
        - agent_role: str
        - message: str (human-readable explanation of the verdict)
        - score_contribution: float (positive = confidence boost, negative = confidence drop)
        - verdict: str (one of: approve, caution, flag, reject, strong_approve)
        - data: dict (the raw signals this agent used to reach its verdict)
        """
        ...

    def _build_result(
        self,
        message: str,
        score: float,
        verdict: str,
        data: dict,
    ) -> dict:
        """Builds the standard agent output dict."""
        return {
            "agent_name": self.name,
            "agent_role": self.role,
            "message": message,
            "score_contribution": score,
            "verdict": verdict,
            "data": data,
        }
