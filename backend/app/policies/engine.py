"""YAML/DB policy loader with deterministic enforcement precedence."""

from __future__ import annotations

from typing import Any

import yaml
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import PolicyRecord


PRECEDENCE = {"ALLOW": 0, "WARN": 1, "EDIT": 2, "HOLD": 3, "BLOCK": 4}
THRESHOLD_TO_DECISION = {"warn": "WARN", "edit": "EDIT", "review": "HOLD", "block": "BLOCK"}


class PolicyEngine:
    def load(self, application: str, db: Session | None = None) -> dict[str, Any]:
        if db is not None:
            record = db.scalar(
                select(PolicyRecord)
                .where(PolicyRecord.application_id == application)
                .order_by(desc(PolicyRecord.version))
                .limit(1)
            )
            if record:
                return dict(record.config)
        path = settings.policy_dir / f"{application}.yaml"
        if not path.exists():
            raise ValueError(f"Unknown application policy: {application}")
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def evaluate(
        self,
        risks: dict[str, float],
        overall_risk: float,
        policy: dict[str, Any],
        signal_codes: set[str] | None = None,
    ) -> tuple[str, list[str]]:
        decision = "ALLOW"
        reasons: list[str] = []
        values = dict(risks)
        values["overall"] = overall_risk
        for dimension, score in values.items():
            thresholds = policy.get("rules", {}).get(dimension, {})
            for threshold_name in ("warn", "edit", "review", "block"):
                threshold = thresholds.get(threshold_name)
                if threshold is not None and score >= float(threshold):
                    candidate = THRESHOLD_TO_DECISION[threshold_name]
                    if PRECEDENCE[candidate] > PRECEDENCE[decision]:
                        decision = candidate
                    reasons.append(
                        f"{dimension} risk {score:.2f} exceeded {threshold_name.upper()} threshold {float(threshold):.2f}"
                    )
        required = set(policy.get("human_review", {}).get("required_for", []))
        matched = required & (signal_codes or set())
        if matched and PRECEDENCE["HOLD"] > PRECEDENCE[decision]:
            decision = "HOLD"
            reasons.append(f"Human review required for policy condition: {', '.join(sorted(matched))}")
        if not reasons:
            reasons.append("All configured risk thresholds remained below intervention levels")
        return decision, reasons
