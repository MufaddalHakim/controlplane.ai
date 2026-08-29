def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["demo_mode"] is True


def test_chat_edit_masks_audit_and_stores_policy_version(client):
    response = client.post("/api/v1/chat", json={"prompt": "privacy scenario", "scenario": "pii_leak", "application": "customer_support", "model_id": "mock-standard", "deep_checks": False})
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "EDIT"
    assert "[EMAIL]" in body["final_response"]
    incident = next(item for item in client.get("/api/v1/incidents").json() if item["trace_id"] == body["trace_id"])
    assert "mira.rao@example.test" not in incident["original_response"]
    assert incident["policy"]["version"] >= 1


def test_check_external_text(client):
    response = client.post("/api/v1/check", json={"response": "Project Atlas launched in March 2024.", "application": "decision_support", "deep_checks": False})
    assert response.status_code == 200
    assert response.json()["claims"][0]["status"] == "CONTRADICTED"


def test_review_queue_and_decision(client):
    held = client.post("/api/v1/chat", json={"prompt": "bias pair", "scenario": "bias", "application": "decision_support", "model_id": "mock-standard", "deep_checks": False}).json()
    assert held["decision"] == "HOLD"
    case_id = held["review_case_id"]
    queue = client.get("/api/v1/reviews?status=pending").json()
    assert any(case["id"] == case_id for case in queue)
    decision = client.post(f"/api/v1/reviews/{case_id}/decision", json={"action": "APPROVE_EDITED", "note": "Synthetic demonstration review", "reviewer": "qa.reviewer"})
    assert decision.status_code == 200
    assert decision.json()["status"] == "resolved"


def test_model_calibration_records_unavailable_uncertainty(client):
    response = client.post("/api/v1/models/mock-standard/calibrate")
    assert response.status_code == 200
    assert response.json()["calibration"]["baseline_uncertainty"] == "Unavailable for this adapter"
