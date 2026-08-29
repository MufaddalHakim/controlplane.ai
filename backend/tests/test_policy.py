from app.policies.engine import PolicyEngine


def policy():
    return {
        "application": "test",
        "version": 1,
        "rules": {
            "privacy": {"warn": 0.2, "edit": 0.4, "review": 0.7, "block": 0.9},
            "hallucination": {"warn": 0.3, "review": 0.6, "block": 0.95},
            "bias": {"review": 0.5},
            "overall": {"warn": 0.5, "review": 0.8, "block": 0.98},
        },
        "human_review": {"required_for": []},
    }


def decide(risks, overall=0.0):
    return PolicyEngine().evaluate(risks, overall, policy())[0]


def test_allow_warn_edit_review_and_block():
    assert decide({"privacy": 0.1}) == "ALLOW"
    assert decide({"privacy": 0.25}) == "WARN"
    assert decide({"privacy": 0.5}) == "EDIT"
    assert decide({"privacy": 0.75}) == "HOLD"
    assert decide({"privacy": 0.95}) == "BLOCK"


def test_precedence_keeps_strongest_action():
    assert decide({"privacy": 0.5, "hallucination": 0.7}) == "HOLD"
    assert decide({"privacy": 0.95, "hallucination": 0.7}) == "BLOCK"


def test_same_score_different_application_policy(client):
    payload = {"prompt": "Policy contrast", "scenario": "hallucination", "model_id": "mock-standard", "deep_checks": False}
    customer = client.post("/api/v1/chat", json={**payload, "application": "customer_support"}).json()
    decision = client.post("/api/v1/chat", json={**payload, "application": "decision_support"}).json()
    assert customer["risks"] == decision["risks"]
    assert customer["decision"] == "WARN"
    assert decision["decision"] == "HOLD"
