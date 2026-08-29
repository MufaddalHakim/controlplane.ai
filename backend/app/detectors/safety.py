"""Small configurable gross-safety signal kept separate from primary Track 1 risks."""

from __future__ import annotations

import re
from time import perf_counter

from app.detectors.base import severity_for
from app.schemas import DetectorSignal


class SafetyDetector:
    name = "safety.basic_patterns"
    patterns = {
        "credential_abuse": re.compile(r"\b(?:steal|exfiltrate)\b.{0,40}\b(?:password|credential|token)s?\b", re.I),
        "disable_controls": re.compile(r"\b(?:disable|bypass)\b.{0,30}\b(?:audit|security|safety)\b", re.I),
    }

    def detect(self, text: str) -> DetectorSignal:
        started = perf_counter()
        hits = [{"category": name, "masked_match": "[SAFETY SIGNAL]"} for name, pattern in self.patterns.items() if pattern.search(text)]
        score = 0.88 if hits else 0.0
        return DetectorSignal(
            detector=self.name,
            risk_type="safety",
            score=score,
            confidence=0.88 if hits else 0.8,
            severity=severity_for(score),
            signals=hits,
            recommended_action="review" if hits else "allow",
            latency_ms=round((perf_counter() - started) * 1000, 3),
        )
