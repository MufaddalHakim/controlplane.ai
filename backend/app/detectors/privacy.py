"""PII and secret detection with span-aware readable redaction."""

from __future__ import annotations

import re
from dataclasses import dataclass
from time import perf_counter

from app.detectors.base import severity_for
from app.schemas import DetectorSignal, Evidence


@dataclass
class Entity:
    entity_type: str
    start: int
    end: int
    confidence: float
    masked: str
    secret: bool = False


class PrivacyDetector:
    name = "privacy.regex"

    PATTERNS = [
        ("BEARER_TOKEN", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{16,}"), 0.99, True),
        ("API_KEY", re.compile(r"\b(?:sk|pk|api)[-_][A-Za-z0-9_-]{16,}\b", re.I), 0.99, True),
        ("AWS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), 0.99, True),
        ("EMAIL", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I), 0.96, False),
        ("IP_ADDRESS", re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"), 0.94, False),
        ("CUSTOMER_ID", re.compile(r"\b(?:CUST|USER|CLIENT|SYN)-\d{4,10}\b", re.I), 0.96, False),
        ("CARD_CANDIDATE", re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"), 0.95, False),
        ("PHONE", re.compile(r"(?<![\w.])(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]?)?\d{3,5}[\s.-]?\d{4,5}(?![\w.])"), 0.86, False),
    ]

    @staticmethod
    def _luhn(value: str) -> bool:
        digits = [int(c) for c in value if c.isdigit()]
        if len(digits) < 13 or len(digits) > 19:
            return False
        if digits[0] == 0 or len(set(digits)) == 1:
            return False
        checksum = 0
        parity = len(digits) % 2
        for index, digit in enumerate(digits):
            if index % 2 == parity:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        return checksum % 10 == 0

    def entities(self, text: str) -> list[Entity]:
        found: list[Entity] = []
        occupied: list[tuple[int, int]] = []
        for entity_type, pattern, confidence, secret in self.PATTERNS:
            for match in pattern.finditer(text):
                if entity_type == "CARD_CANDIDATE" and not self._luhn(match.group()):
                    continue
                if entity_type == "PHONE" and not 10 <= len(re.sub(r"\D", "", match.group())) <= 12:
                    continue
                if any(match.start() < end and match.end() > start for start, end in occupied):
                    continue
                actual_type = "CREDIT_CARD" if entity_type == "CARD_CANDIDATE" else entity_type
                found.append(Entity(actual_type, match.start(), match.end(), confidence, f"[{actual_type}]", secret))
                occupied.append((match.start(), match.end()))
        return sorted(found, key=lambda item: item.start)

    def redact(self, text: str) -> str:
        entities = self.entities(text)
        redacted = text
        for entity in reversed(entities):
            redacted = redacted[: entity.start] + entity.masked + redacted[entity.end :]
        return redacted

    def detect(self, text: str) -> DetectorSignal:
        started = perf_counter()
        entities = self.entities(text)
        secret_count = sum(1 for entity in entities if entity.secret)
        pii_count = len(entities) - secret_count
        if secret_count:
            score = 0.99
            action = "block"
        elif pii_count >= 3:
            score = 0.88
            action = "redact"
        elif pii_count == 2:
            score = 0.78
            action = "redact"
        elif pii_count == 1:
            score = 0.62
            action = "redact"
        else:
            score = 0.0
            action = "allow"
        masked_signals = [
            {
                "entity_type": entity.entity_type,
                "start": entity.start,
                "end": entity.end,
                "confidence": entity.confidence,
                "masked": entity.masked,
            }
            for entity in entities
        ]
        evidence = [
            Evidence(
                source_id=f"span:{entity.start}-{entity.end}",
                source_name="response span",
                snippet=entity.masked,
                masked_value=entity.masked,
            )
            for entity in entities
        ]
        return DetectorSignal(
            detector=self.name,
            risk_type="privacy",
            score=score,
            confidence=max((entity.confidence for entity in entities), default=0.99),
            severity=severity_for(score),
            signals=masked_signals,
            evidence=evidence,
            recommended_action=action,
            latency_ms=round((perf_counter() - started) * 1000, 3),
        )
