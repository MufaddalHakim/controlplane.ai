"""End-to-end ControlPlane tiered evaluation and enforcement runtime."""

from __future__ import annotations

import hashlib
import uuid
from time import perf_counter
from typing import Any

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.base import estimate_tokens
from app.adapters.mock import MockModelAdapter
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import (
    ApplicationProfile,
    EvidenceItemRecord,
    Interaction,
    ReviewCase,
    RiskAssessment,
    RiskSignalRecord,
)
from app.detectors.confidential import ConfidentialDetector
from app.detectors.cost import CostDetector
from app.detectors.fairness import FairnessDetector
from app.detectors.grounding import GroundingDetector, hedge_unsupported
from app.detectors.privacy import PrivacyDetector
from app.detectors.safety import SafetyDetector
from app.detectors.self_consistency import analyze_consistency
from app.policies.engine import PolicyEngine
from app.risk.aggregator import aggregate
from app.schemas import CheckRequest, ModelResult, RuntimeResponse
from app.services.session_risk import previous_session_context, update_session_state


class ControlPlaneRuntime:
    """Model-independent inline gate with asynchronous Tier 2 enrichment."""

    def __init__(self) -> None:
        self.privacy = PrivacyDetector()
        self.confidential = ConfidentialDetector()
        self.grounding = GroundingDetector()
        self.fairness = FairnessDetector()
        self.cost = CostDetector()
        self.safety = SafetyDetector()
        self.policy_engine = PolicyEngine()

    async def assess(
        self,
        *,
        prompt: str,
        model_result: ModelResult,
        application: str,
        session_id: str,
        context: dict[str, Any],
        db: Session,
        background_tasks: BackgroundTasks | None = None,
        deep_checks: bool = True,
    ) -> RuntimeResponse:
        total_started = perf_counter()
        policy = self.policy_engine.load(application, db)
        app = db.get(ApplicationProfile, application)
        if app is None:
            raise ValueError(f"Unknown application: {application}")

        tier0_started = perf_counter()
        privacy = self.privacy.detect(model_result.text)
        confidential = self.confidential.detect(model_result.text)
        safety = self.safety.detect(model_result.text)
        adapter = MockModelAdapter(model_result.model_name)
        model_cost = adapter.estimate_cost(model_result.input_tokens, model_result.output_tokens) if model_result.provider == "mock" else float(model_result.metadata.get("model_cost_usd", 0))
        cost = self.cost.detect(input_tokens=model_result.input_tokens, output_tokens=model_result.output_tokens, model_cost=model_cost, policy=policy, model_name=model_result.model_name)
        tier0_latency = (perf_counter() - tier0_started) * 1000

        tier1_started = perf_counter()
        grounding, claims = self.grounding.detect(model_result.text)
        fairness_metadata = dict(model_result.metadata)
        fairness_metadata.update(context)
        fairness = self.fairness.detect(fairness_metadata)
        session_context = previous_session_context(db, session_id)
        if session_context["elevated"] and grounding.score >= 0.5:
            grounding.score = round(min(1.0, grounding.score + 0.12), 3)
            grounding.signals.append({"session_escalation": True, "explanation": session_context["explanation"]})
        signals = [privacy, confidential, safety, cost, grounding, fairness]
        risks, overall = aggregate(signals, policy.get("weights", {}))
        signal_codes = set()
        if fairness.score >= 0.5:
            signal_codes.add("severe_bias_signal")
        if application == "decision_support" and (grounding.score >= 0.55 or fairness.score >= 0.5):
            signal_codes.add("important_decision")
        decision, reasons = self.policy_engine.evaluate(risks, overall, policy, signal_codes)
        tier1_latency = (perf_counter() - tier1_started) * 1000

        redacted = self.confidential.redact(self.privacy.redact(model_result.text))
        final_response = model_result.text
        editing_action = "none"
        if risks["privacy"] >= float(policy.get("rules", {}).get("privacy", {}).get("edit", 1.1)):
            final_response = redacted
            editing_action = "privacy_redaction"
        if decision == "EDIT" and risks["hallucination"] >= float(policy.get("rules", {}).get("hallucination", {}).get("edit", 1.1)):
            final_response = hedge_unsupported(final_response, claims)
            editing_action = "claim_hedging"
        if decision == "BLOCK":
            final_response = "Response blocked by ControlPlane policy. No model content was delivered."
            editing_action = "blocked_delivery"

        trace_id = f"cp-{uuid.uuid4().hex[:12]}"
        interaction_id = uuid.uuid4().hex
        response_for_audit = model_result.text if settings.audit_store_raw else redacted
        prompt_for_audit = prompt if settings.audit_store_raw else self.privacy.redact(prompt)
        review_case_id = None
        review_status = "not_required"
        if decision == "HOLD":
            review_case_id = f"rev-{uuid.uuid4().hex[:10]}"
            review_status = "pending"
        total_latency = (perf_counter() - total_started) * 1000 + model_result.latency_ms
        deep_status = "queued" if deep_checks and background_tasks is not None else "not_requested"
        interaction = Interaction(
            id=interaction_id,
            trace_id=trace_id,
            application_id=application,
            model_id=model_result.model_name,
            session_id=session_id,
            prompt_masked=prompt_for_audit,
            response_masked=response_for_audit,
            response_hash=hashlib.sha256(model_result.text.encode("utf-8")).hexdigest(),
            final_response=final_response,
            policy_name=policy["application"],
            policy_version=int(policy["version"]),
            machine_decision=decision,
            final_decision=decision,
            editing_action=editing_action,
            review_status=review_status,
            overall_risk=overall,
            risks=risks,
            input_tokens=model_result.input_tokens,
            output_tokens=model_result.output_tokens,
            model_cost_usd=model_cost,
            checker_cost_usd=0.0,
            model_latency_ms=model_result.latency_ms,
            tier0_latency_ms=round(tier0_latency, 3),
            tier1_latency_ms=round(tier1_latency, 3),
            total_latency_ms=round(total_latency, 3),
            deep_status=deep_status,
            detector_names=[signal.detector for signal in signals],
            triggered_rules=reasons,
        )
        db.add(interaction)
        db.add(RiskAssessment(interaction_id=interaction_id, overall_risk=overall, risk_breakdown=risks))
        evidence_items = []
        for signal in signals:
            db.add(RiskSignalRecord(interaction_id=interaction_id, detector=signal.detector, risk_type=signal.risk_type, score=signal.score, confidence=signal.confidence, severity=signal.severity, masked_signals=signal.signals, latency_ms=signal.latency_ms))
            for item in signal.evidence:
                evidence_items.append(item)
                db.add(EvidenceItemRecord(interaction_id=interaction_id, source_id=item.source_id, source_name=item.source_name, snippet=item.snippet, similarity=item.similarity, metadata_json=item.metadata))
        if review_case_id:
            db.add(ReviewCase(id=review_case_id, interaction_id=interaction_id, priority="critical" if overall >= 0.85 else "high", reason="; ".join(reasons), proposed_response=final_response))
        update_session_state(db, session_id, session_context, decision)
        db.commit()

        scenario = str(model_result.metadata.get("scenario", "safe"))
        if deep_status == "queued" and background_tasks is not None:
            background_tasks.add_task(self._deep_analysis, interaction_id, prompt, scenario, model_result.model_name)

        return RuntimeResponse(
            trace_id=trace_id,
            application={"id": app.id, "name": app.name, "risk_tier": app.risk_tier, "latency_budget_ms": app.latency_budget_ms},
            model={"id": model_result.model_name, "provider": model_result.provider, "capabilities": adapter.capabilities().model_dump() if model_result.provider == "mock" else {"text_output": True}},
            original_response=model_result.text,
            final_response=final_response,
            decision=decision,
            overall_risk=overall,
            risks=risks,
            signals=signals,
            claims=claims,
            evidence=evidence_items,
            policy={"name": policy["application"], "version": policy["version"], "risk_tier": policy.get("metadata", {}).get("risk_tier")},
            triggered_rules=reasons,
            session_risk=session_context,
            performance={"model_latency_ms": model_result.latency_ms, "tier0_latency_ms": round(tier0_latency, 3), "tier1_latency_ms": round(tier1_latency, 3), "controlplane_latency_ms": round(tier0_latency + tier1_latency, 3), "total_latency_ms": round(total_latency, 3), "latency_budget_ms": app.latency_budget_ms},
            cost={"model_cost_usd": model_cost, "risk_check_cost_usd": 0.0, "total_ai_cost_usd": model_cost, "pricing_notice": "Illustrative - configurable."},
            deep_check={"status": deep_status, "detector": "performance.self_consistency" if deep_status == "queued" else None},
            review_case_id=review_case_id,
        )

    async def check(self, request: CheckRequest, db: Session, background_tasks: BackgroundTasks | None = None) -> RuntimeResponse:
        result = ModelResult(
            text=request.response,
            input_tokens=request.input_tokens or estimate_tokens(request.prompt),
            output_tokens=request.output_tokens or estimate_tokens(request.response),
            latency_ms=0.0,
            model_name=request.model_id,
            provider="external",
            metadata={"model_cost_usd": 0.0, **request.context},
        )
        return await self.assess(prompt=request.prompt, model_result=result, application=request.application, session_id=request.session_id or f"external-{uuid.uuid4().hex[:8]}", context=request.context, db=db, background_tasks=background_tasks, deep_checks=request.deep_checks)

    async def _deep_analysis(self, interaction_id: str, prompt: str, scenario: str, model_name: str) -> None:
        adapter = MockModelAdapter(model_name if model_name.startswith("mock") else "mock-standard")
        samples = await adapter.consistency_samples(prompt, scenario, count=3)
        result = analyze_consistency(samples)
        with SessionLocal() as db:
            interaction = db.get(Interaction, interaction_id)
            if interaction:
                interaction.deep_status = "complete"
                interaction.deep_result = result
                db.commit()
