"""Offline lexical retrieval and claim/evidence verification."""

from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from time import perf_counter

from app.core.config import settings
from app.detectors.base import severity_for
from app.schemas import ClaimAssessment, DetectorSignal, Evidence


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to", "was", "were", "with",
}
MONTHS = "january|february|march|april|may|june|july|august|september|october|november|december"


def _tokens(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", text.lower()) if token not in STOPWORDS]


def _cosine(left: str, right: str) -> float:
    a, b = Counter(_tokens(left)), Counter(_tokens(right))
    if not a or not b:
        return 0.0
    numerator = sum(value * b.get(key, 0) for key, value in a.items())
    denominator = math.sqrt(sum(value * value for value in a.values())) * math.sqrt(
        sum(value * value for value in b.values())
    )
    return numerator / denominator if denominator else 0.0


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\$?\d+(?:\.\d+)?(?:\s*(?:million|billion|percent|%))?", text.lower()))


def _dates(text: str) -> set[str]:
    return set(re.findall(rf"\b(?:{MONTHS})\s+\d{{4}}\b", text.lower()))


class GroundingDetector:
    name = "grounding.lexical_verifier"

    def __init__(self, knowledge_dir: Path | None = None) -> None:
        source_dir = knowledge_dir or settings.knowledge_dir
        self.sentences: list[tuple[str, str, str]] = []
        for path in sorted(source_dir.glob("*.md")):
            text = re.sub(r"^#+\s+.*$", "", path.read_text(encoding="utf-8"), flags=re.M)
            for index, sentence in enumerate(re.split(r"(?<=[.!?])\s+", text)):
                clean = sentence.strip()
                if len(clean) >= 20:
                    self.sentences.append((f"{path.stem}:{index}", path.name, clean))

    def extract_claims(self, answer: str) -> list[str]:
        expanded = re.sub(
            r"\s+and\s+(generated|earned|recorded|cost|launched|reached|includes|supports)\b",
            r". \1",
            answer,
            flags=re.I,
        )
        sentences = [item.strip(" \n\t\"'") for item in re.split(r"(?<=[.!?])\s+", expanded)]
        factual = []
        for sentence in sentences:
            has_number = bool(re.search(r"\d|\$|%", sentence))
            has_named_entity = bool(re.search(r"\b(?:Project|NovaPhone|NovaHome|Northstar|Atlas)\b", sentence))
            has_claim_verb = bool(re.search(r"\b(?:launched|generated|recorded|includes|supports|receive|lasts|is|are|costs|reached)\b", sentence, re.I))
            if len(sentence.split()) >= 3 and (has_number or (has_named_entity and has_claim_verb)):
                factual.append(sentence.rstrip("."))
        return factual

    def assess_claim(self, claim: str) -> ClaimAssessment:
        ranked = sorted(
            ((round(_cosine(claim, sentence), 4), source_id, source_name, sentence) for source_id, source_name, sentence in self.sentences),
            reverse=True,
        )
        similarity, source_id, source_name, evidence = ranked[0] if ranked else (0.0, None, None, "")
        claim_dates, evidence_dates = _dates(claim), _dates(evidence)
        claim_numbers, evidence_numbers = _numbers(claim), _numbers(evidence)
        subject_overlap = bool(set(_tokens(claim)[:3]) & set(_tokens(evidence)))
        claim_token_set = set(_tokens(claim))
        token_coverage = len(claim_token_set & set(_tokens(evidence))) / max(1, len(claim_token_set))

        if (similarity >= 0.72 or token_coverage >= 0.85) and (not claim_numbers or claim_numbers <= evidence_numbers):
            status = "SUPPORTED"
            confidence = min(0.99, 0.72 + similarity * 0.27)
            explanation = "The available source closely supports this claim."
        elif claim_dates and evidence_dates and claim_dates.isdisjoint(evidence_dates) and similarity >= 0.42 and subject_overlap:
            status = "CONTRADICTED"
            confidence = min(0.98, 0.72 + similarity * 0.25)
            explanation = "Available evidence contains a conflicting date for the same subject."
        elif similarity >= 0.55 and not (claim_numbers - evidence_numbers):
            status = "PARTIALLY_SUPPORTED"
            confidence = min(0.9, 0.55 + similarity * 0.3)
            explanation = "The source supports part, but not all, of this claim."
        elif similarity >= 0.22 or claim_numbers:
            status = "UNSUPPORTED"
            confidence = min(0.92, 0.58 + similarity * 0.28)
            explanation = "No supporting evidence was found in the available knowledge base."
        else:
            status = "INSUFFICIENT_EVIDENCE"
            confidence = 0.62
            explanation = "The available sources are insufficient to assess this claim."
        return ClaimAssessment(
            claim=claim,
            status=status,
            confidence=round(confidence, 3),
            source_id=source_id,
            source_name=source_name,
            evidence_snippet=evidence or None,
            explanation=explanation,
        )

    def detect(self, answer: str) -> tuple[DetectorSignal, list[ClaimAssessment]]:
        started = perf_counter()
        claims = [self.assess_claim(claim) for claim in self.extract_claims(answer)]
        if not claims:
            risk = 0.08
        else:
            contradicted = sum(claim.status == "CONTRADICTED" for claim in claims)
            unsupported = sum(claim.status == "UNSUPPORTED" for claim in claims)
            partial = sum(claim.status == "PARTIALLY_SUPPORTED" for claim in claims)
            insufficient = sum(claim.status == "INSUFFICIENT_EVIDENCE" for claim in claims)
            if contradicted and unsupported:
                risk = 0.72
            elif contradicted:
                risk = 0.68
            elif unsupported:
                risk = 0.64 if unsupported == 1 else 0.70
            elif insufficient:
                risk = 0.34
            elif partial:
                risk = 0.38
            else:
                risk = 0.05
        evidence = [
            Evidence(
                source_id=claim.source_id or "none",
                source_name=claim.source_name or "No source",
                snippet=claim.evidence_snippet or "No supporting evidence found.",
                similarity=round(_cosine(claim.claim, claim.evidence_snippet or ""), 3),
                metadata={"status": claim.status, "claim": claim.claim},
            )
            for claim in claims
        ]
        supported = sum(claim.status == "SUPPORTED" for claim in claims)
        contradicted = sum(claim.status == "CONTRADICTED" for claim in claims)
        signal_data = [{"claim": claim.claim, "status": claim.status, "confidence": claim.confidence} for claim in claims]
        signal_data.append({
            "supported_claim_ratio": round(supported / max(1, len(claims)), 3),
            "contradicted_claim_ratio": round(contradicted / max(1, len(claims)), 3),
            "evidence_coverage": round(sum(claim.source_id is not None for claim in claims) / max(1, len(claims)), 3),
        })
        action = "review" if risk >= 0.68 else ("warn" if risk >= 0.34 else "allow")
        return DetectorSignal(
            detector=self.name,
            risk_type="hallucination",
            score=risk,
            confidence=round(sum(claim.confidence for claim in claims) / max(1, len(claims)), 3) if claims else 0.72,
            severity=severity_for(risk),
            signals=signal_data,
            evidence=evidence,
            recommended_action=action,
            latency_ms=round((perf_counter() - started) * 1000, 3),
        ), claims


def hedge_unsupported(answer: str, claims: list[ClaimAssessment]) -> str:
    """Replace unsupported sentences with an explicit non-fabricating hedge."""

    output = answer
    for claim in claims:
        if claim.status in {"UNSUPPORTED", "CONTRADICTED"}:
            pattern = re.compile(re.escape(claim.claim) + r"\.?")
            output = pattern.sub("I could not verify this claim from the available sources.", output)
    return re.sub(r"\s+", " ", output).strip()
