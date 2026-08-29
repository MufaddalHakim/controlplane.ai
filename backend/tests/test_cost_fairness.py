from app.detectors.cost import CostDetector
from app.detectors.fairness import FairnessDetector


POLICY = {"budgets": {"preferred_request_usd": 0.01, "soft_cost_usd": 0.015, "hard_cost_usd": 0.05, "output_tokens": 700}}


def cost(value: float, tokens: int = 100):
    return CostDetector().detect(input_tokens=20, output_tokens=tokens, model_cost=value, policy=POLICY, model_name="mock-premium")


def test_cost_below_soft_and_hard_thresholds():
    assert cost(0.005).score < 0.6
    assert 0.6 <= cost(0.02).score < 0.95
    assert cost(0.06).score == 0.95


def pair(changed: bool):
    return {"fairness_pair": {"attribute": "gender", "profile_a": {"decision": "advance", "score": 0.8, "sentiment": 0.6}, "profile_b": {"decision": "reject" if changed else "advance", "score": 0.35 if changed else 0.79, "sentiment": -0.1 if changed else 0.58}}}


def test_counterfactual_consistent_pair():
    assert FairnessDetector().detect(pair(False)).score < 0.1


def test_counterfactual_inconsistent_pair():
    signal = FairnessDetector().detect(pair(True))
    assert signal.score >= 0.5
    assert "not proof" in signal.signals[0]["notice"].lower()
