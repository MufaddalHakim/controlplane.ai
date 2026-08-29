"""Exact and near-duplicate matching against a synthetic confidential corpus."""

from __future__ import annotations

import json
import re
from time import perf_counter

from app.core.config import settings
from app.detectors.base import severity_for
from app.schemas import DetectorSignal, Evidence


def _shingles(text: str, size: int = 4) -> set[str]:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    return {normalized[i : i + size] for i in range(max(0, len(normalized) - size + 1))}


class ConfidentialDetector:
    name = "privacy.confidential_corpus"

    def __init__(self) -> None:
        self.corpus = json.loads(settings.confidential_file.read_text(encoding="utf-8"))

    def detect(self, text: str) -> DetectorSignal:
        started = perf_counter()
        normalized = text.lower()
        matches = []
        evidence: list[Evidence] = []
        best = 0.0
        for item in self.corpus:
            phrase = item["text"]
            exact = phrase.lower() in normalized
            source_shingles = _shingles(phrase)
            response_shingles = _shingles(text)
            similarity = (
                len(source_shingles & response_shingles) / max(1, len(source_shingles))
            )
            if exact or similarity >= 0.72:
                score = 0.99 if item["severity"] == "critical" else max(0.78, similarity)
                best = max(best, score)
                matches.append({"source": item["id"], "label": item["label"], "match": "exact" if exact else "near_duplicate", "similarity": round(similarity, 3), "masked": "[CONFIDENTIAL]"})
                evidence.append(Evidence(source_id=item["id"], source_name=item["label"], snippet="[CONFIDENTIAL MATCH]", similarity=round(similarity, 3), masked_value="[CONFIDENTIAL]"))
        return DetectorSignal(
            detector=self.name,
            risk_type="privacy",
            score=round(best, 3),
            confidence=0.98 if matches else 0.92,
            severity=severity_for(best),
            signals=matches,
            evidence=evidence,
            recommended_action="block" if best >= 0.9 else ("redact" if matches else "allow"),
            latency_ms=round((perf_counter() - started) * 1000, 3),
        )

    def redact(self, text: str) -> str:
        output = text
        for item in self.corpus:
            output = re.sub(re.escape(item["text"]), "[CONFIDENTIAL]", output, flags=re.I)
        return output
