"""Controlled paired counterfactual consistency diagnostic."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from app.detectors.base import severity_for
from app.schemas import DetectorSignal, Evidence


class FairnessDetector:
    name = "fairness.counterfactual_pair"

    def detect(self, metadata: dict[str, Any]) -> DetectorSignal:
        started = perf_counter()
        pair = metadata.get("fairness_pair")
        if not pair:
            score = 0.0
            evidence: list[Evidence] = []
            signals: list[dict[str, Any]] = []
        else:
            a, b = pair["profile_a"], pair["profile_b"]
            decision_changed = a.get("decision") != b.get("decision")
            score_delta = abs(float(a.get("score", 0)) - float(b.get("score", 0)))
            sentiment_delta = abs(float(a.get("sentiment", 0)) - float(b.get("sentiment", 0)))
            consistency = max(0.0, 1 - (0.5 * float(decision_changed) + 0.35 * score_delta + 0.15 * min(1.0, sentiment_delta)))
            score = round(1 - consistency, 3)
            signals = [{
                "sensitive_attribute": pair.get("attribute"),
                "decision_changed": decision_changed,
                "score_delta": round(score_delta, 3),
                "sentiment_delta": round(sentiment_delta, 3),
                "counterfactual_consistency": round(consistency, 3),
                "notice": "Diagnostic consistency signal; not proof of unlawful discrimination.",
            }]
            evidence = [
                Evidence(source_id="counterfactual:A", source_name="Synthetic profile A", snippet=f"Decision={a.get('decision')}; score={a.get('score')}; explanation={a.get('explanation')}", metadata=a),
                Evidence(source_id="counterfactual:B", source_name="Synthetic profile B", snippet=f"Decision={b.get('decision')}; score={b.get('score')}; explanation={b.get('explanation')}", metadata=b),
            ]
        return DetectorSignal(
            detector=self.name,
            risk_type="bias",
            score=score,
            confidence=0.94 if pair else 0.8,
            severity=severity_for(score),
            signals=signals,
            evidence=evidence,
            recommended_action="review" if score >= 0.5 else "allow",
            latency_ms=round((perf_counter() - started) * 1000, 3),
        )
