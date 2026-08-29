"""Exercise the complete scripted demo against a running backend."""

from __future__ import annotations

import sys
import time

import httpx


BASE_URL = "http://127.0.0.1:8000/api/v1"


def chat(client: httpx.Client, scenario: str, application: str, model_id: str = "mock-standard", session_id: str | None = None):
    response = client.post(
        "/chat",
        json={
            "prompt": f"End-to-end verification: {scenario}",
            "scenario": scenario,
            "application": application,
            "model_id": model_id,
            "session_id": session_id,
            "deep_checks": True,
        },
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    expected = [
        ("safe", "customer_support", "mock-standard", "ALLOW"),
        ("pii_leak", "customer_support", "mock-standard", "EDIT"),
        ("secret_leak", "internal_copilot", "mock-standard", "BLOCK"),
        ("hallucination", "internal_copilot", "mock-standard", "EDIT"),
        ("bias", "decision_support", "mock-standard", "HOLD"),
        ("cost", "customer_support", "mock-premium", "WARN"),
    ]
    with httpx.Client(base_url=BASE_URL, timeout=30) as client:
        assert client.get("/health").json()["status"] == "healthy"
        client.post("/demo/reset").raise_for_status()
        results = {}
        for scenario, application, model_id, decision in expected:
            result = chat(client, scenario, application, model_id)
            assert result["decision"] == decision, (scenario, result["decision"], result["triggered_rules"])
            results[scenario] = result
            print(f"PASS {scenario:16} -> {decision}")

        customer = chat(client, "hallucination", "customer_support")
        simulated = client.post("/policies/simulate", json={"application": "decision_support", "risks": customer["risks"]}).json()
        assert customer["decision"] == "WARN" and simulated["decision"] == "HOLD"
        assert customer["risks"]["hallucination"] == simulated["risks"]["hallucination"] == 0.72
        print("PASS policy contrast  -> WARN / HOLD with identical 0.72 score")

        multi = [chat(client, "multi_turn", "decision_support", session_id="verify-multi") for _ in range(3)]
        assert multi[-1]["session_risk"]["elevated"] is True
        print("PASS multi-turn risk  -> elevated on third turn")

        case_id = results["bias"]["review_case_id"]
        resolved = client.post(f"/reviews/{case_id}/decision", json={"action": "APPROVE_EDITED", "note": "End-to-end synthetic verification", "reviewer": "verify.script"})
        resolved.raise_for_status()
        assert resolved.json()["status"] == "resolved"
        print("PASS review workflow  -> resolved with audit note")

        evaluation = client.post("/evaluation/run")
        evaluation.raise_for_status()
        assert evaluation.json()["case_count"] == 80
        print("PASS evaluation       -> 80 actual cases")

        summary = client.get("/analytics/summary").json()
        assert summary["requests"] >= len(expected)
        assert client.get("/models").status_code == 200
        assert client.get("/incidents").status_code == 200
        print("PASS analytics/audit  -> stored backend data")

        trace_id = results["safe"]["trace_id"]
        for _ in range(10):
            incident = next(row for row in client.get("/incidents").json() if row["trace_id"] == trace_id)
            if incident["deep_check"]["status"] == "complete":
                break
            time.sleep(0.1)
        assert incident["deep_check"]["status"] == "complete"
        print("PASS async deep check -> audit event updated")

    print("\nAll mandatory backend demo paths passed end to end.")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, httpx.HTTPError) as exc:
        print(f"Verification failed: {exc}", file=sys.stderr)
        raise
