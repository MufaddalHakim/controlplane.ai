"""Run real detector metrics over the labeled synthetic dataset."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import Any

from sqlalchemy.orm import Session

from app.analytics.queries import percentile
from app.core.config import settings
from app.db.models import EvaluationRun
from app.detectors.cost import CostDetector
from app.detectors.fairness import FairnessDetector
from app.detectors.grounding import GroundingDetector
from app.detectors.privacy import PrivacyDetector
from app.policies.engine import PolicyEngine


def _classification(scores: list[float], labels: list[bool], threshold: float) -> dict[str, float | int]:
    tp = sum(score >= threshold and label for score, label in zip(scores, labels))
    tn = sum(score < threshold and not label for score, label in zip(scores, labels))
    fp = sum(score >= threshold and not label for score, label in zip(scores, labels))
    fn = sum(score < threshold and label for score, label in zip(scores, labels))
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn, "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(2 * precision * recall / max(0.000001, precision + recall), 3), "false_positive_rate": round(fp / max(1, fp + tn), 3), "false_negative_rate": round(fn / max(1, fn + tp), 3), "positive_rate": round((tp + fp) / max(1, len(labels)), 3), "threshold": threshold}


def run_evaluation(db: Session, write_artifacts: bool = True) -> dict[str, Any]:
    cases = json.loads(settings.evaluation_file.read_text(encoding="utf-8"))
    privacy = PrivacyDetector()
    grounding = GroundingDetector()
    fairness = FairnessDetector()
    cost = CostDetector()
    policy = PolicyEngine().load("customer_support", db)
    scores: dict[str, list[float]] = {key: [] for key in ("privacy", "hallucination", "bias", "cost")}
    labels: dict[str, list[bool]] = {key: [] for key in scores}
    latencies: list[float] = []
    for case in cases:
        started = perf_counter()
        privacy_signal = privacy.detect(case["response"])
        grounding_signal, _ = grounding.detect(case["response"])
        fairness_signal = fairness.detect(case.get("context", {}))
        cost_signal = cost.detect(input_tokens=int(case.get("input_tokens", 20)), output_tokens=int(case.get("output_tokens", 40)), model_cost=float(case.get("model_cost_usd", 0.0001)), policy=policy, model_name=case.get("model", "mock-standard"))
        signals = {"privacy": privacy_signal, "hallucination": grounding_signal, "bias": fairness_signal, "cost": cost_signal}
        for detector, signal in signals.items():
            scores[detector].append(signal.score)
            labels[detector].append(bool(case.get("labels", {}).get(detector, False)))
        latencies.append((perf_counter() - started) * 1000)
    thresholds = {"privacy": 0.5, "hallucination": 0.5, "bias": 0.5, "cost": 0.6}
    detector_metrics = {detector: _classification(scores[detector], labels[detector], thresholds[detector]) for detector in scores}
    threshold_analysis = []
    for threshold in (0.30, 0.45, 0.60, 0.72, 0.85):
        row = _classification(scores["privacy"], labels["privacy"], threshold)
        threshold_analysis.append({"detector": "privacy", **row, "review_escalation_rate": row["positive_rate"]})
    report = {
        "run_id": f"eval-{uuid.uuid4().hex[:10]}",
        "case_count": len(cases),
        "detectors": detector_metrics,
        "threshold_analysis": threshold_analysis,
        "latency": {"mean_ms": round(mean(latencies), 3), "p50_ms": percentile(latencies, 0.5), "p95_ms": percentile(latencies, 0.95)},
        "methodology": "Metrics are calculated from actual local detector runs over labeled synthetic cases.",
    }
    db.add(EvaluationRun(id=report["run_id"], case_count=len(cases), metrics=report, mean_latency_ms=report["latency"]["mean_ms"], p50_latency_ms=report["latency"]["p50_ms"], p95_latency_ms=report["latency"]["p95_ms"]))
    db.commit()
    if write_artifacts:
        artifact_dir = settings.root_dir / "artifacts"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        (artifact_dir / "evaluation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        lines = ["# ControlPlane.ai Evaluation Report", "", f"Actual cases executed: **{len(cases)}**", "", "## Detector metrics", "", "| Detector | Precision | Recall | F1 | FPR | FNR |", "|---|---:|---:|---:|---:|---:|"]
        for detector, metric in detector_metrics.items():
            lines.append(f"| {detector} | {metric['precision']:.3f} | {metric['recall']:.3f} | {metric['f1']:.3f} | {metric['false_positive_rate']:.3f} | {metric['false_negative_rate']:.3f} |")
        lines.extend(["", "## Privacy threshold tradeoff", "", "| Threshold | Precision | Recall | FPR | Escalation rate |", "|---:|---:|---:|---:|---:|"])
        for row in threshold_analysis:
            lines.append(f"| {row['threshold']:.2f} | {row['precision']:.3f} | {row['recall']:.3f} | {row['false_positive_rate']:.3f} | {row['review_escalation_rate']:.3f} |")
        lines.extend(["", "Lower thresholds catch more labeled risks but increase reviewer volume. Higher thresholds reduce review volume while increasing missed-case risk.", "", f"Latency: mean {report['latency']['mean_ms']:.3f} ms, P50 {report['latency']['p50_ms']:.3f} ms, P95 {report['latency']['p95_ms']:.3f} ms."])
        (artifact_dir / "evaluation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report
