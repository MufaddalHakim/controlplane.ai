"""Normalized audit, policy, review, model, and evaluation records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ApplicationProfile(Base):
    __tablename__ = "application_profiles"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    risk_tier: Mapped[str] = mapped_column(String(32))
    latency_budget_ms: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class PolicyRecord(Base):
    __tablename__ = "policies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(Integer)
    config: Mapped[dict[str, Any]] = mapped_column(JSON)
    change_note: Mapped[str] = mapped_column(Text, default="Initial policy")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ModelProfile(Base):
    __tablename__ = "model_profiles"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64))
    model_name: Mapped[str] = mapped_column(String(128))
    capability_level: Mapped[str] = mapped_column(String(64))
    context_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_per_million_usd: Mapped[float] = mapped_column(Float, default=0)
    output_per_million_usd: Mapped[float] = mapped_column(Float, default=0)
    usage_available: Mapped[bool] = mapped_column(Boolean, default=False)
    logprobs_available: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CalibrationProfile(Base):
    __tablename__ = "calibration_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_id: Mapped[str] = mapped_column(ForeignKey("model_profiles.id"), index=True)
    prompt_count: Mapped[int] = mapped_column(Integer)
    baseline_latency_ms: Mapped[float] = mapped_column(Float)
    baseline_output_tokens: Mapped[float] = mapped_column(Float)
    baseline_cost_usd: Mapped[float] = mapped_column(Float)
    uncertainty_available: Mapped[bool] = mapped_column(Boolean, default=False)
    baseline_uncertainty: Mapped[float | None] = mapped_column(Float, nullable=True)
    calibrated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Interaction(Base):
    __tablename__ = "interactions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    trace_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    application_id: Mapped[str] = mapped_column(String(64), index=True)
    model_id: Mapped[str] = mapped_column(String(100), index=True)
    session_id: Mapped[str] = mapped_column(String(100), index=True)
    prompt_masked: Mapped[str] = mapped_column(Text)
    response_masked: Mapped[str] = mapped_column(Text)
    response_hash: Mapped[str] = mapped_column(String(64))
    final_response: Mapped[str] = mapped_column(Text)
    policy_name: Mapped[str] = mapped_column(String(64))
    policy_version: Mapped[int] = mapped_column(Integer)
    machine_decision: Mapped[str] = mapped_column(String(24), index=True)
    final_decision: Mapped[str] = mapped_column(String(24), index=True)
    editing_action: Mapped[str] = mapped_column(String(64), default="none")
    review_status: Mapped[str] = mapped_column(String(32), default="not_required")
    overall_risk: Mapped[float] = mapped_column(Float, index=True)
    risks: Mapped[dict[str, float]] = mapped_column(JSON)
    input_tokens: Mapped[int] = mapped_column(Integer)
    output_tokens: Mapped[int] = mapped_column(Integer)
    model_cost_usd: Mapped[float] = mapped_column(Float)
    checker_cost_usd: Mapped[float] = mapped_column(Float, default=0)
    model_latency_ms: Mapped[float] = mapped_column(Float)
    tier0_latency_ms: Mapped[float] = mapped_column(Float)
    tier1_latency_ms: Mapped[float] = mapped_column(Float)
    total_latency_ms: Mapped[float] = mapped_column(Float)
    deep_status: Mapped[str] = mapped_column(String(32), default="not_requested")
    deep_result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    detector_names: Mapped[list[str]] = mapped_column(JSON)
    triggered_rules: Mapped[list[str]] = mapped_column(JSON)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interaction_id: Mapped[str] = mapped_column(ForeignKey("interactions.id"), index=True)
    overall_risk: Mapped[float] = mapped_column(Float)
    risk_breakdown: Mapped[dict[str, float]] = mapped_column(JSON)
    aggregation_method: Mapped[str] = mapped_column(String(64), default="weighted_noisy_or")


class RiskSignalRecord(Base):
    __tablename__ = "risk_signals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interaction_id: Mapped[str] = mapped_column(ForeignKey("interactions.id"), index=True)
    detector: Mapped[str] = mapped_column(String(100), index=True)
    risk_type: Mapped[str] = mapped_column(String(32), index=True)
    score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String(24))
    masked_signals: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    latency_ms: Mapped[float] = mapped_column(Float)


class EvidenceItemRecord(Base):
    __tablename__ = "evidence_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interaction_id: Mapped[str] = mapped_column(ForeignKey("interactions.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(128))
    source_name: Mapped[str] = mapped_column(String(256))
    snippet: Mapped[str] = mapped_column(Text)
    similarity: Mapped[float] = mapped_column(Float)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class ReviewCase(Base):
    __tablename__ = "review_cases"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    interaction_id: Mapped[str] = mapped_column(ForeignKey("interactions.id"), unique=True)
    priority: Mapped[str] = mapped_column(String(24), default="high")
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    reason: Mapped[str] = mapped_column(Text)
    proposed_response: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReviewDecision(Base):
    __tablename__ = "review_decisions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("review_cases.id"), index=True)
    action: Mapped[str] = mapped_column(String(40))
    reviewer: Mapped[str] = mapped_column(String(120))
    note: Mapped[str] = mapped_column(Text)
    edited_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_machine_decision: Mapped[str] = mapped_column(String(24))
    policy_version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interaction_id: Mapped[str] = mapped_column(ForeignKey("interactions.id"), index=True)
    label: Mapped[str] = mapped_column(String(40), index=True)
    note: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SessionRiskState(Base):
    __tablename__ = "session_risk_states"
    session_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    rolling_risk: Mapped[float] = mapped_column(Float, default=0)
    recent_event_count: Mapped[int] = mapped_column(Integer, default=0)
    elevated_reason: Mapped[str] = mapped_column(Text, default="")
    previous_decisions: Mapped[list[str]] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EvaluationCase(Base):
    __tablename__ = "evaluation_cases"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    input_text: Mapped[str] = mapped_column(Text)
    response_text: Mapped[str] = mapped_column(Text)
    application_id: Mapped[str] = mapped_column(String(64))
    labels: Mapped[dict[str, Any]] = mapped_column(JSON)
    expected_intervention: Mapped[str | None] = mapped_column(String(24), nullable=True)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    case_count: Mapped[int] = mapped_column(Integer)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON)
    mean_latency_ms: Mapped[float] = mapped_column(Float)
    p50_latency_ms: Mapped[float] = mapped_column(Float)
    p95_latency_ms: Mapped[float] = mapped_column(Float)
