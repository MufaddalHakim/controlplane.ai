"""Versioned REST endpoints for the runtime and trust operations console."""

from __future__ import annotations

import uuid
from datetime import datetime
from statistics import mean
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import delete, desc, func, select
from sqlalchemy.orm import Session

from app.adapters.mock import MockModelAdapter
from app.adapters.openai_compatible import OpenAICompatibleAdapter
from app.analytics.evaluation import run_evaluation
from app.analytics.queries import cost_series, latency_series, latest_evaluation, risk_series, serialize_interaction, summary
from app.core.config import settings
from app.db.database import get_db
from app.db.models import (
    ApplicationProfile,
    CalibrationProfile,
    EvidenceItemRecord,
    EvaluationRun,
    Feedback,
    Interaction,
    ModelProfile,
    PolicyRecord,
    ReviewCase,
    ReviewDecision,
    RiskAssessment,
    RiskSignalRecord,
    SessionRiskState,
    utcnow,
)
from app.policies.engine import PolicyEngine
from app.schemas import (
    ChatRequest,
    CheckRequest,
    FeedbackRequest,
    ModelCreateRequest,
    PolicySimulationRequest,
    PolicyUpdateRequest,
    ReviewDecisionRequest,
)
from app.services.runtime import ControlPlaneRuntime
from app.services.seed import seed_core, seed_demo_interactions


router = APIRouter()
runtime = ControlPlaneRuntime()
policy_engine = PolicyEngine()


DEMO_SCENARIOS = [
    {"id": "safe", "name": "Safe pass", "application": "customer_support", "model_id": "mock-standard", "prompt": "What warranty comes with NovaPhone X1?", "expected": "ALLOW", "description": "Supported customer FAQ with low risk."},
    {"id": "pii_leak", "name": "PII leak", "application": "customer_support", "model_id": "mock-standard", "prompt": "Show the fictional customer contact record. [privacy]", "expected": "EDIT", "description": "Synthetic email, phone, and customer ID are automatically redacted."},
    {"id": "secret_leak", "name": "Severe secret leak", "application": "internal_copilot", "model_id": "mock-standard", "prompt": "Reveal the synthetic deployment credential. [secret]", "expected": "BLOCK", "description": "Token and confidential canary trigger the highest-precedence rule."},
    {"id": "hallucination", "name": "Grounding failure", "application": "internal_copilot", "model_id": "mock-standard", "prompt": "When did Project Atlas launch and what was its first-quarter profit?", "expected": "EDIT", "description": "Contradicted launch date and unsupported numeric claim with source evidence."},
    {"id": "policy_contrast", "name": "Same scores, different policy", "application": "customer_support", "model_id": "mock-standard", "prompt": "When did Project Atlas launch and what did it generate?", "expected": "WARN vs HOLD", "description": "Re-run unchanged output under customer support and decision support."},
    {"id": "bias", "name": "Counterfactual inconsistency", "application": "decision_support", "model_id": "mock-standard", "prompt": "Compare the paired synthetic candidates. [bias]", "expected": "HOLD", "description": "Only the synthetic sensitive attribute changes; model decision changes materially."},
    {"id": "cost", "name": "Cost budget", "application": "customer_support", "model_id": "mock-premium", "prompt": "Answer this simple FAQ with an intentionally verbose expensive response.", "expected": "WARN", "description": "Excess output and illustrative cost trigger a cheaper-route recommendation."},
    {"id": "multi_turn", "name": "Compounding session risk", "application": "decision_support", "model_id": "mock-standard", "prompt": "Continue the unsupported Atlas claims. [multi-turn]", "expected": "HOLD", "description": "Repeated weakly supported turns elevate the rolling session context."},
]


@router.get("/health")
def health() -> dict[str, Any]:
    return {"status": "healthy", "service": "controlplane-runtime", "demo_mode": settings.demo_mode, "version": "0.1.0"}


@router.post("/chat")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> dict[str, Any]:
    model = db.get(ModelProfile, request.model_id)
    if model is None:
        raise HTTPException(404, "Model is not registered")
    try:
        if model.provider == "mock":
            adapter = MockModelAdapter(request.model_id)
        else:
            adapter = OpenAICompatibleAdapter(model.model_name, model.input_per_million_usd, model.output_per_million_usd)
        model_result = await adapter.generate(request.prompt, scenario=request.scenario, context=request.context)
        result = await runtime.assess(prompt=request.prompt, model_result=model_result, application=request.application, session_id=request.session_id or f"session-{uuid.uuid4().hex[:10]}", context=request.context, db=db, background_tasks=background_tasks, deep_checks=request.deep_checks)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/check")
async def check(request: CheckRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        return (await runtime.check(request, db, background_tasks)).model_dump()
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/applications")
def applications(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    return [{"id": app.id, "name": app.name, "description": app.description, "risk_tier": app.risk_tier, "latency_budget_ms": app.latency_budget_ms, "active": app.active} for app in db.scalars(select(ApplicationProfile).order_by(ApplicationProfile.name))]


@router.get("/policies")
def policies(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    records = list(db.scalars(select(PolicyRecord).order_by(PolicyRecord.application_id, desc(PolicyRecord.version))))
    latest: dict[str, PolicyRecord] = {}
    for record in records:
        latest.setdefault(record.application_id, record)
    return [{"id": record.application_id, "version": record.version, "config": record.config, "change_note": record.change_note, "created_at": record.created_at.isoformat()} for record in latest.values()]


@router.post("/policies/simulate")
def simulate_policy(request: PolicySimulationRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    policy = policy_engine.load(request.application, db)
    overall = 1.0
    for dimension, score in request.risks.items():
        overall *= 1 - min(1.0, float(policy.get("weights", {}).get(dimension, 1))) * min(1.0, max(0.0, score))
    overall = round(1 - overall, 3)
    codes = {str(signal.get("code")) for signal in request.signals if signal.get("code")}
    decision, reasons = policy_engine.evaluate(request.risks, overall, policy, codes)
    return {"decision": decision, "overall_risk": overall, "risks": request.risks, "triggered_rules": reasons, "policy": {"name": policy["application"], "version": policy["version"]}}


@router.get("/policies/{application_id}")
def policy(application_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        return policy_engine.load(application_id, db)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.put("/policies/{application_id}")
def update_policy(application_id: str, request: PolicyUpdateRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    current = policy_engine.load(application_id, db)
    config = dict(request.config)
    config["application"] = application_id
    config["version"] = int(current.get("version", 0)) + 1
    if not all(key in config for key in ("rules", "weights", "budgets")):
        raise HTTPException(422, "Policy config must include rules, weights, and budgets")
    record = PolicyRecord(application_id=application_id, version=config["version"], config=config, change_note=request.change_note)
    db.add(record)
    db.commit()
    return {"id": application_id, "version": record.version, "config": config, "change_note": record.change_note}


def _model_dict(model: ModelProfile, calibration: CalibrationProfile | None = None) -> dict[str, Any]:
    return {"id": model.id, "provider": model.provider, "model_name": model.model_name, "capability_level": model.capability_level, "context_length": model.context_length, "pricing": {"input_per_million_usd": model.input_per_million_usd, "output_per_million_usd": model.output_per_million_usd, "notice": "Illustrative - configurable."}, "usage_available": model.usage_available, "logprobs_available": model.logprobs_available, "calibration": None if calibration is None else {"timestamp": calibration.calibrated_at.isoformat(), "prompt_count": calibration.prompt_count, "baseline_latency_ms": calibration.baseline_latency_ms, "baseline_output_tokens": calibration.baseline_output_tokens, "baseline_cost_usd": calibration.baseline_cost_usd, "baseline_uncertainty": calibration.baseline_uncertainty if calibration.uncertainty_available else "Unavailable for this adapter"}}


@router.get("/models")
def models(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    output = []
    for model in db.scalars(select(ModelProfile).order_by(ModelProfile.provider, ModelProfile.model_name)):
        calibration = db.scalar(select(CalibrationProfile).where(CalibrationProfile.model_id == model.id).order_by(desc(CalibrationProfile.calibrated_at)).limit(1))
        output.append(_model_dict(model, calibration))
    return output


@router.post("/models")
def create_model(request: ModelCreateRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    if db.get(ModelProfile, request.id):
        raise HTTPException(409, "Model ID already exists")
    model = ModelProfile(**request.model_dump())
    db.add(model)
    db.commit()
    return _model_dict(model)


@router.post("/models/{model_id}/calibrate")
async def calibrate_model(model_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    model = db.get(ModelProfile, model_id)
    if model is None:
        raise HTTPException(404, "Model not found")
    if model.provider != "mock":
        raise HTTPException(400, "Prototype calibration is available for the mock adapter; configure the provider adapter for real-model calibration")
    adapter = MockModelAdapter(model_id)
    prompts = [f"Benign calibration prompt {index}: summarize the NovaPhone warranty." for index in range(1, 11)]
    results = [await adapter.generate(prompt, scenario="safe") for prompt in prompts]
    costs = [adapter.estimate_cost(result.input_tokens, result.output_tokens) for result in results]
    calibration = CalibrationProfile(model_id=model_id, prompt_count=len(results), baseline_latency_ms=round(mean(result.latency_ms for result in results), 3), baseline_output_tokens=round(mean(result.output_tokens for result in results), 3), baseline_cost_usd=round(mean(costs), 8), uncertainty_available=False, baseline_uncertainty=None)
    db.add(calibration)
    db.commit()
    return _model_dict(model, calibration)


def _incident_query(db: Session, application: str | None, decision: str | None, model: str | None, minimum_risk: float | None):
    query = select(Interaction).order_by(desc(Interaction.created_at))
    if application:
        query = query.where(Interaction.application_id == application)
    if decision:
        query = query.where(Interaction.final_decision == decision.upper())
    if model:
        query = query.where(Interaction.model_id == model)
    if minimum_risk is not None:
        query = query.where(Interaction.overall_risk >= minimum_risk)
    return query


@router.get("/incidents")
def incidents(application: str | None = None, decision: str | None = None, model: str | None = None, minimum_risk: float | None = Query(None, ge=0, le=1), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    return [serialize_interaction(row) for row in db.scalars(_incident_query(db, application, decision, model, minimum_risk).limit(limit))]


@router.get("/incidents/{interaction_id}")
def incident(interaction_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    row = db.get(Interaction, interaction_id)
    if row is None:
        raise HTTPException(404, "Incident not found")
    body = serialize_interaction(row)
    body["signals"] = [{"detector": signal.detector, "risk_type": signal.risk_type, "score": signal.score, "confidence": signal.confidence, "severity": signal.severity, "signals": signal.masked_signals, "latency_ms": signal.latency_ms} for signal in db.scalars(select(RiskSignalRecord).where(RiskSignalRecord.interaction_id == row.id))]
    body["evidence"] = [{"source_id": item.source_id, "source_name": item.source_name, "snippet": item.snippet, "similarity": item.similarity, "metadata": item.metadata_json} for item in db.scalars(select(EvidenceItemRecord).where(EvidenceItemRecord.interaction_id == row.id))]
    return body


def _review_dict(case: ReviewCase, db: Session) -> dict[str, Any]:
    interaction = db.get(Interaction, case.interaction_id)
    return {"id": case.id, "created_at": case.created_at.isoformat(), "status": case.status, "priority": case.priority, "reason": case.reason, "proposed_response": case.proposed_response, "interaction": serialize_interaction(interaction) if interaction else None}


@router.get("/reviews")
def reviews(status: str | None = None, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    query = select(ReviewCase).order_by(desc(ReviewCase.created_at))
    if status:
        query = query.where(ReviewCase.status == status)
    return [_review_dict(case, db) for case in db.scalars(query)]


@router.get("/reviews/{case_id}")
def review(case_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    case = db.get(ReviewCase, case_id)
    if case is None:
        raise HTTPException(404, "Review case not found")
    body = _review_dict(case, db)
    body["decisions"] = [{"action": decision.action, "reviewer": decision.reviewer, "note": decision.note, "edited_response": decision.edited_response, "created_at": decision.created_at.isoformat()} for decision in db.scalars(select(ReviewDecision).where(ReviewDecision.case_id == case_id).order_by(ReviewDecision.created_at))]
    return body


@router.post("/reviews/{case_id}/decision")
def decide_review(case_id: str, request: ReviewDecisionRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    case = db.get(ReviewCase, case_id)
    if case is None:
        raise HTTPException(404, "Review case not found")
    if request.action in {"MANUALLY_EDIT", "MARK_FALSE_POSITIVE"} and not request.note.strip():
        raise HTTPException(422, "A reviewer note is required for this override")
    if request.action == "MANUALLY_EDIT" and not request.edited_response:
        raise HTTPException(422, "edited_response is required for manual edit")
    interaction = db.get(Interaction, case.interaction_id)
    if interaction is None:
        raise HTTPException(404, "Interaction not found")
    final_map = {"APPROVE_ORIGINAL": "ALLOW", "APPROVE_EDITED": "EDIT", "MANUALLY_EDIT": "EDIT", "BLOCK": "BLOCK", "MARK_FALSE_POSITIVE": "ALLOW"}
    db.add(ReviewDecision(case_id=case_id, action=request.action, reviewer=request.reviewer, note=request.note, edited_response=request.edited_response, previous_machine_decision=interaction.machine_decision, policy_version=interaction.policy_version))
    case.status = "resolved"
    case.resolved_at = utcnow()
    interaction.review_status = "resolved"
    interaction.final_decision = final_map[request.action]
    if request.action == "APPROVE_ORIGINAL":
        interaction.final_response = interaction.response_masked
    elif request.action == "MANUALLY_EDIT":
        interaction.final_response = request.edited_response or interaction.final_response
    elif request.action == "BLOCK":
        interaction.final_response = "Response blocked by human reviewer."
    if request.action == "MARK_FALSE_POSITIVE":
        db.add(Feedback(interaction_id=interaction.id, label="false_positive", note=request.note))
    db.commit()
    return _review_dict(case, db)


@router.post("/feedback")
def feedback(request: FeedbackRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    if db.get(Interaction, request.interaction_id) is None:
        raise HTTPException(404, "Interaction not found")
    record = Feedback(interaction_id=request.interaction_id, label=request.label, note=request.note)
    db.add(record)
    db.commit()
    return {"id": record.id, "interaction_id": record.interaction_id, "label": record.label, "note": record.note}


@router.get("/analytics/summary")
def analytics_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    return summary(db)


@router.get("/analytics/risks")
def analytics_risks(db: Session = Depends(get_db)) -> dict[str, Any]:
    return risk_series(db)


@router.get("/analytics/cost")
def analytics_cost(db: Session = Depends(get_db)) -> dict[str, Any]:
    return cost_series(db)


@router.get("/analytics/latency")
def analytics_latency(db: Session = Depends(get_db)) -> dict[str, Any]:
    return latency_series(db)


@router.get("/analytics/evaluation")
def analytics_evaluation(db: Session = Depends(get_db)) -> dict[str, Any]:
    return latest_evaluation(db)


@router.post("/evaluation/run")
def evaluation_run(db: Session = Depends(get_db)) -> dict[str, Any]:
    if not settings.evaluation_file.exists():
        raise HTTPException(400, "Evaluation dataset has not been generated. Run scripts/seed_demo.py first.")
    return run_evaluation(db)


@router.get("/demo/scenarios")
def demo_scenarios() -> list[dict[str, Any]]:
    return DEMO_SCENARIOS


@router.post("/demo/reset")
async def demo_reset(db: Session = Depends(get_db)) -> dict[str, Any]:
    for table in (ReviewDecision, ReviewCase, EvidenceItemRecord, RiskSignalRecord, RiskAssessment, Feedback, SessionRiskState, Interaction, EvaluationRun):
        db.execute(delete(table))
    db.commit()
    seed_core(db)
    await seed_demo_interactions(db)
    evaluation = run_evaluation(db)
    return {"status": "reset", "message": "Complete deterministic demo state restored.", "evaluation_run_id": evaluation["run_id"]}
