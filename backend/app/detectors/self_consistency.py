"""Asynchronous lexical self-consistency analysis."""

from __future__ import annotations

import itertools
import re
from time import perf_counter


def _token_set(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _jaccard(left: str, right: str) -> float:
    a, b = _token_set(left), _token_set(right)
    return len(a & b) / max(1, len(a | b))


def analyze_consistency(samples: list[str]) -> dict[str, object]:
    started = perf_counter()
    pairs = [_jaccard(a, b) for a, b in itertools.combinations(samples, 2)]
    similarity = sum(pairs) / max(1, len(pairs))
    number_sets = [set(re.findall(r"\d+(?:\.\d+)?", sample)) for sample in samples]
    entity_disagreement = len({tuple(sorted(numbers)) for numbers in number_sets}) > 1
    risk = min(1.0, (1 - similarity) * 0.75 + (0.25 if entity_disagreement else 0))
    return {
        "detector": "performance.self_consistency",
        "sample_count": len(samples),
        "mean_similarity": round(similarity, 3),
        "important_entity_disagreement": entity_disagreement,
        "uncertainty_risk": round(risk, 3),
        "samples": samples,
        "latency_ms": round((perf_counter() - started) * 1000, 3),
        "notice": "Disagreement is an uncertainty signal, not proof that any sample is false.",
    }
