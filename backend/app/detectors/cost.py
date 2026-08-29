"""Request-budget and output-length risk accounting."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from app.detectors.base import severity_for
from app.schemas import DetectorSignal, Evidence


class CostDetector:
    name = "cost.request_budget"

    def detect(
        self,
        *,
        input_tokens: int,
        output_tokens: int,
        model_cost: float,
        policy: dict[str, Any],
        model_name: str,
    ) -> DetectorSignal:
        started = perf_counter()
        budgets = policy.get("budgets", {})
        preferred = float(budgets.get("preferred_request_usd", 0.01))
        soft = float(budgets.get("soft_cost_usd", preferred * 1.5))
        hard = float(budgets.get("hard_cost_usd", preferred * 5))
        output_budget = int(budgets.get("output_tokens", 1000))
        cost_ratio = model_cost / max(preferred, 0.000001)
        token_ratio = output_tokens / max(output_budget, 1)
        if model_cost < soft and cost_ratio <= 0.2 and token_ratio <= 0.2:
            score = 0.0
        elif model_cost >= hard:
            score = 0.95
        elif model_cost >= soft:
            score = min(0.92, 0.64 + 0.18 * max(0.0, cost_ratio - 1.0))
        elif token_ratio > 1:
            score = min(0.85, 0.55 + 0.2 * (token_ratio - 1))
        else:
            score = min(0.45, 0.25 * max(cost_ratio, token_ratio))
        recommendation = None
        if score >= 0.6 and model_name != "mock-economy":
            recommendation = "Potential lower-cost route: mock-economy. Evaluate quality before use."
        signals = [{
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "output_token_budget": output_budget,
            "model_cost_usd": round(model_cost, 8),
            "preferred_request_usd": preferred,
            "soft_cost_usd": soft,
            "hard_cost_usd": hard,
            "relative_budget_use": round(cost_ratio, 3),
            "pricing_notice": "Illustrative - configurable.",
            "recommendation": recommendation,
        }]
        evidence = [Evidence(source_id="policy-budget", source_name="Configured request budget", snippet=f"${model_cost:.6f} used of ${preferred:.6f} preferred budget", metadata=signals[0])]
        return DetectorSignal(
            detector=self.name,
            risk_type="cost",
            score=round(score, 3),
            confidence=0.99,
            severity=severity_for(score),
            signals=signals,
            evidence=evidence,
            recommended_action="warn" if score >= 0.6 else "allow",
            latency_ms=round((perf_counter() - started) * 1000, 3),
        )
