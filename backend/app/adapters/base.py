"""Provider-neutral model adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.schemas import ModelCapabilities, ModelResult


def estimate_tokens(text: str) -> int:
    """Use a documented local approximation when provider usage is unavailable."""

    return max(1, round(len(text.split()) * 1.3))


class ModelAdapter(ABC):
    @abstractmethod
    async def generate(
        self, prompt: str, *, scenario: str | None = None, context: dict[str, Any] | None = None
    ) -> ModelResult:
        """Generate one normalized model response."""

    @abstractmethod
    def capabilities(self) -> ModelCapabilities:
        """Describe signals supplied by this adapter without inventing unavailable data."""

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate inference cost from configurable pricing."""
