"""Dimension-preserving weighted noisy-OR aggregation."""

from __future__ import annotations

from app.schemas import DetectorSignal


RISK_DIMENSIONS = ("hallucination", "privacy", "bias", "safety", "cost")


def aggregate(signals: list[DetectorSignal], weights: dict[str, float]) -> tuple[dict[str, float], float]:
    """Keep max detector risk per dimension, then combine using weighted noisy-OR."""

    risks = {dimension: 0.0 for dimension in RISK_DIMENSIONS}
    for signal in signals:
        risks[signal.risk_type] = max(risks[signal.risk_type], signal.score)
    survival = 1.0
    for dimension, score in risks.items():
        weight = min(1.0, max(0.0, float(weights.get(dimension, 1.0))))
        survival *= 1 - weight * score
    return {key: round(value, 3) for key, value in risks.items()}, round(1 - survival, 3)
