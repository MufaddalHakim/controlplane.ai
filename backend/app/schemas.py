"""Pydantic contracts exposed by the API and detector pipeline."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


Decision = Literal["ALLOW", "WARN", "EDIT", "HOLD", "BLOCK"]


class ModelCapabilities(BaseModel):
    text_output: bool = True
    token_usage: bool = False
    logprobs: bool = False
    attention: bool = False
    streaming: bool = False


class ModelResult(BaseModel):
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    model_name: str
    provider: str
    logprobs: list[float] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    source_id: str
    source_name: str
    snippet: str
    similarity: float = 0.0
    masked_value: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DetectorSignal(BaseModel):
    detector: str
    risk_type: Literal["hallucination", "privacy", "bias", "safety", "cost"]
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    severity: Literal["none", "low", "medium", "high", "critical"]
    signals: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    recommended_action: str = "allow"
    latency_ms: float = 0.0


class ClaimAssessment(BaseModel):
    claim: str
    status: Literal[
        "SUPPORTED",
        "PARTIALLY_SUPPORTED",
        "UNSUPPORTED",
        "CONTRADICTED",
        "INSUFFICIENT_EVIDENCE",
    ]
    confidence: float
    source_id: str | None = None
    source_name: str | None = None
    evidence_snippet: str | None = None
    explanation: str


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    application: str = "customer_support"
    model_id: str = "mock-standard"
    scenario: str | None = None
    session_id: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    deep_checks: bool = True


class CheckRequest(BaseModel):
    response: str = Field(min_length=1, max_length=30000)
    prompt: str = "Externally generated response"
    application: str = "customer_support"
    model_id: str = "external-text-only"
    session_id: str | None = None
    input_tokens: int = 0
    output_tokens: int | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    deep_checks: bool = False


class ReviewDecisionRequest(BaseModel):
    action: Literal[
        "APPROVE_ORIGINAL",
        "APPROVE_EDITED",
        "MANUALLY_EDIT",
        "BLOCK",
        "MARK_FALSE_POSITIVE",
    ]
    note: str = ""
    edited_response: str | None = None
    reviewer: str = "demo.reviewer"


class FeedbackRequest(BaseModel):
    interaction_id: str
    label: Literal[
        "correct_flag",
        "false_positive",
        "missed_issue",
        "incorrect_severity",
        "useful_intervention",
        "unnecessary_intervention",
    ]
    note: str = ""


class ModelCreateRequest(BaseModel):
    id: str
    provider: str
    model_name: str
    capability_level: str = "text_only"
    context_length: int | None = None
    input_per_million_usd: float = 0.0
    output_per_million_usd: float = 0.0
    usage_available: bool = False
    logprobs_available: bool = False


class PolicyUpdateRequest(BaseModel):
    config: dict[str, Any]
    change_note: str = "Thresholds updated in Policy Studio"


class PolicySimulationRequest(BaseModel):
    application: str
    risks: dict[str, float]
    signals: list[dict[str, Any]] = Field(default_factory=list)


class RuntimeResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    trace_id: str
    application: dict[str, Any]
    model: dict[str, Any]
    original_response: str
    final_response: str
    decision: Decision
    overall_risk: float
    risks: dict[str, float]
    signals: list[DetectorSignal]
    claims: list[ClaimAssessment]
    evidence: list[Evidence]
    policy: dict[str, Any]
    triggered_rules: list[str]
    session_risk: dict[str, Any]
    performance: dict[str, Any]
    cost: dict[str, Any]
    deep_check: dict[str, Any]
    review_case_id: str | None = None
