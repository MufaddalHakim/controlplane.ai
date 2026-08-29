"""Idempotent creation of application, model, and policy demo records."""

from __future__ import annotations

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.mock import MockModelAdapter
from app.core.config import settings
from app.db.models import ApplicationProfile, ModelProfile, PolicyRecord
from app.services.runtime import ControlPlaneRuntime


APPLICATIONS = [
    ApplicationProfile(id="customer_support", name="Customer Support", description="Low-latency customer-facing assistance with automatic PII redaction.", risk_tier="medium", latency_budget_ms=50),
    ApplicationProfile(id="internal_copilot", name="Internal Knowledge Copilot", description="Evidence-grounded answers over synthetic enterprise knowledge.", risk_tier="high", latency_budget_ms=120),
    ApplicationProfile(id="decision_support", name="High-Risk Decision Support", description="Synthetic HR/finance diagnostic environment with strict human review.", risk_tier="critical", latency_budget_ms=250),
]


MODELS = [
    ModelProfile(id="mock-standard", provider="mock", model_name="mock-standard", capability_level="text_usage", context_length=32000, input_per_million_usd=0.5, output_per_million_usd=1.5, usage_available=True, logprobs_available=False),
    ModelProfile(id="mock-premium", provider="mock", model_name="mock-premium", capability_level="text_usage", context_length=128000, input_per_million_usd=15.0, output_per_million_usd=60.0, usage_available=True, logprobs_available=False),
    ModelProfile(id="mock-economy", provider="mock", model_name="mock-economy", capability_level="text_usage", context_length=16000, input_per_million_usd=0.1, output_per_million_usd=0.3, usage_available=True, logprobs_available=False),
    ModelProfile(id="external-text-only", provider="external", model_name="external-text-only", capability_level="text_only", context_length=None, input_per_million_usd=0, output_per_million_usd=0, usage_available=False, logprobs_available=False),
]


def seed_core(db: Session) -> None:
    for app in APPLICATIONS:
        if db.get(ApplicationProfile, app.id) is None:
            db.add(app)
    for model in MODELS:
        if db.get(ModelProfile, model.id) is None:
            db.add(model)
    db.flush()
    for path in sorted(settings.policy_dir.glob("*.yaml")):
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        exists = db.scalar(select(PolicyRecord).where(PolicyRecord.application_id == config["application"], PolicyRecord.version == int(config["version"])))
        if exists is None:
            db.add(PolicyRecord(application_id=config["application"], version=int(config["version"]), config=config, change_note="Seeded deterministic demo policy"))
        else:
            exists.config = config
    db.commit()


async def seed_demo_interactions(db: Session) -> None:
    """Create the deterministic telemetry required by the dashboard and review queue."""

    runtime = ControlPlaneRuntime()
    fixtures = [
        ("safe", "customer_support", "mock-standard", "demo-safe"),
        ("pii_leak", "customer_support", "mock-standard", "demo-privacy"),
        ("secret_leak", "internal_copilot", "mock-standard", "demo-secret"),
        ("hallucination", "internal_copilot", "mock-standard", "demo-hallucination"),
        ("hallucination", "customer_support", "mock-standard", "demo-contrast"),
        ("hallucination", "decision_support", "mock-standard", "demo-contrast"),
        ("bias", "decision_support", "mock-standard", "demo-bias"),
        ("cost", "customer_support", "mock-premium", "demo-cost"),
    ]
    for scenario, application, model_id, session_id in fixtures:
        adapter = MockModelAdapter(model_id)
        result = await adapter.generate(f"Seeded {scenario} scenario", scenario=scenario)
        await runtime.assess(prompt=f"Seeded {scenario} scenario", model_result=result, application=application, session_id=session_id, context={}, db=db, background_tasks=None, deep_checks=False)
    for turn in range(3):
        adapter = MockModelAdapter("mock-standard")
        result = await adapter.generate("Repeated unsupported multi-turn claim", scenario="multi_turn")
        await runtime.assess(prompt=f"Multi-turn claim {turn + 1}", model_result=result, application="decision_support", session_id="demo-multi-turn", context={}, db=db, background_tasks=None, deep_checks=False)
