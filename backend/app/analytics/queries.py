"""Aggregate stored telemetry for dashboard and Trust Center APIs."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import EvaluationRun, Feedback, Interaction, ReviewCase


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(percentile_value * len(ordered)) - 1))
    return round(ordered[index], 3)


def serialize_interaction(row: Interaction) -> dict[str, Any]:
    return {
        "id": row.id,
        "trace_id": row.trace_id,
        "created_at": row.created_at.isoformat(),
        "application": row.application_id,
        "model": row.model_id,
        "session_id": row.session_id,
        "prompt": row.prompt_masked,
        "original_response": row.response_masked,
        "final_response": row.final_response,
        "policy": {"name": row.policy_name, "version": row.policy_version},
        "decision": row.final_decision,
        "machine_decision": row.machine_decision,
        "review_status": row.review_status,
        "overall_risk": row.overall_risk,
        "risks": row.risks,
        "tokens": {"input": row.input_tokens, "output": row.output_tokens},
        "cost": {"model": row.model_cost_usd, "checker": row.checker_cost_usd, "total": row.model_cost_usd + row.checker_cost_usd},
        "latency": {"model": row.model_latency_ms, "tier0": row.tier0_latency_ms, "tier1": row.tier1_latency_ms, "total": row.total_latency_ms},
        "deep_check": {"status": row.deep_status, "result": row.deep_result},
        "detectors": row.detector_names,
        "triggered_rules": row.triggered_rules,
        "editing_action": row.editing_action,
    }


def summary(db: Session) -> dict[str, Any]:
    rows = list(db.scalars(select(Interaction).order_by(Interaction.created_at)))
    counts = Counter(row.final_decision for row in rows)
    latencies = [row.total_latency_ms - row.model_latency_ms for row in rows]
    spend = sum(row.model_cost_usd for row in rows)
    checker = sum(row.checker_cost_usd for row in rows)
    pending_reviews = db.scalar(select(ReviewCase).where(ReviewCase.status == "pending"))
    by_application: dict[str, dict[str, Any]] = defaultdict(lambda: {"requests": 0, "risk_total": 0.0, "interventions": 0})
    for row in rows:
        target = by_application[row.application_id]
        target["requests"] += 1
        target["risk_total"] += row.overall_risk
        target["interventions"] += row.final_decision != "ALLOW"
    app_health = [
        {"application": key, "requests": value["requests"], "average_risk": round(value["risk_total"] / max(1, value["requests"]), 3), "intervention_rate": round(value["interventions"] / max(1, value["requests"]), 3)}
        for key, value in by_application.items()
    ]
    return {
        "requests": len(rows),
        "passed": counts["ALLOW"],
        "warned": counts["WARN"],
        "edited": counts["EDIT"],
        "held": counts["HOLD"],
        "blocked": counts["BLOCK"],
        "review_rate": round(counts["HOLD"] / max(1, len(rows)), 3),
        "average_risk": round(mean([row.overall_risk for row in rows]), 3) if rows else 0,
        "p95_controlplane_latency_ms": percentile(latencies, 0.95),
        "ai_spend_usd": round(spend, 6),
        "checker_cost_usd": round(checker, 6),
        "pending_reviews": 0 if pending_reviews is None else 1,
        "intervention_mix": dict(counts),
        "application_health": app_health,
        "recent_incidents": [serialize_interaction(row) for row in list(reversed(rows))[:8]],
    }


def risk_series(db: Session) -> dict[str, Any]:
    rows = list(db.scalars(select(Interaction).order_by(Interaction.created_at)))
    series = [{"timestamp": row.created_at.isoformat(), "application": row.application_id, "overall": row.overall_risk, **row.risks} for row in rows]
    dimensions = {dimension: round(mean([float(row.risks.get(dimension, 0)) for row in rows]), 3) if rows else 0 for dimension in ("hallucination", "privacy", "bias", "safety", "cost")}
    midpoint = len(rows) // 2
    drift = []
    if midpoint >= 3:
        for dimension in dimensions:
            baseline = [float(row.risks.get(dimension, 0)) for row in rows[:midpoint]]
            current = [float(row.risks.get(dimension, 0)) for row in rows[midpoint:]]
            baseline_mean = mean(baseline)
            current_mean = mean(current)
            shift = current_mean - baseline_mean
            drift.append({"dimension": dimension, "baseline_mean": round(baseline_mean, 3), "current_mean": round(current_mean, 3), "absolute_shift": round(shift, 3), "significant": abs(shift) >= 0.20})
    return {"averages": dimensions, "series": series, "drift": drift, "method": "Difference in rolling-window means; monitoring signal only."}


def cost_series(db: Session) -> dict[str, Any]:
    rows = list(db.scalars(select(Interaction).order_by(Interaction.created_at)))
    return {"series": [{"timestamp": row.created_at.isoformat(), "application": row.application_id, "model_cost_usd": row.model_cost_usd, "checker_cost_usd": row.checker_cost_usd, "total_cost_usd": row.model_cost_usd + row.checker_cost_usd, "input_tokens": row.input_tokens, "output_tokens": row.output_tokens} for row in rows], "total_model_cost_usd": round(sum(row.model_cost_usd for row in rows), 6), "total_checker_cost_usd": round(sum(row.checker_cost_usd for row in rows), 6), "pricing_notice": "Illustrative - configurable."}


def latency_series(db: Session) -> dict[str, Any]:
    rows = list(db.scalars(select(Interaction).order_by(Interaction.created_at)))
    overhead = [row.tier0_latency_ms + row.tier1_latency_ms for row in rows]
    return {"series": [{"timestamp": row.created_at.isoformat(), "model_ms": row.model_latency_ms, "tier0_ms": row.tier0_latency_ms, "tier1_ms": row.tier1_latency_ms, "total_ms": row.total_latency_ms} for row in rows], "mean_controlplane_ms": round(mean(overhead), 3) if overhead else 0, "p50_controlplane_ms": percentile(overhead, 0.5), "p95_controlplane_ms": percentile(overhead, 0.95)}


def latest_evaluation(db: Session) -> dict[str, Any]:
    run = db.scalar(select(EvaluationRun).order_by(desc(EvaluationRun.created_at)).limit(1))
    if run is None:
        return {"status": "not_run", "detectors": {}, "threshold_analysis": []}
    return {"status": "complete", "run_id": run.id, "created_at": run.created_at.isoformat(), "case_count": run.case_count, "detectors": run.metrics.get("detectors", {}), "threshold_analysis": run.metrics.get("threshold_analysis", []), "intervention_accuracy": run.metrics.get("intervention_accuracy", {}), "latency": {"mean_ms": run.mean_latency_ms, "p50_ms": run.p50_latency_ms, "p95_ms": run.p95_latency_ms}}
