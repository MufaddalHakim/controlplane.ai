"""Optional HTTP adapter for OpenAI-compatible chat-completions providers."""

from __future__ import annotations

from time import perf_counter
from typing import Any

import httpx

from app.adapters.base import ModelAdapter, estimate_tokens
from app.core.config import settings
from app.schemas import ModelCapabilities, ModelResult


class OpenAICompatibleAdapter(ModelAdapter):
    def __init__(self, model_name: str, input_rate: float = 0.0, output_rate: float = 0.0) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when Demo Mode is disabled for this adapter")
        self.model_name = model_name
        self.input_rate = input_rate
        self.output_rate = output_rate

    async def generate(
        self, prompt: str, *, scenario: str | None = None, context: dict[str, Any] | None = None
    ) -> ModelResult:
        started = perf_counter()
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        payload = {"model": self.model_name, "messages": [{"role": "user", "content": prompt}]}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.openai_base_url.rstrip('/')}/chat/completions", headers=headers, json=payload
            )
            response.raise_for_status()
            body = response.json()
        text = body["choices"][0]["message"]["content"]
        usage = body.get("usage") or {}
        return ModelResult(
            text=text,
            input_tokens=int(usage.get("prompt_tokens") or estimate_tokens(prompt)),
            output_tokens=int(usage.get("completion_tokens") or estimate_tokens(text)),
            latency_ms=round((perf_counter() - started) * 1000, 3),
            model_name=self.model_name,
            provider="openai-compatible",
            logprobs=body["choices"][0].get("logprobs"),
            metadata={"usage_estimated": not bool(usage)},
        )

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(text_output=True, token_usage=True, logprobs=False, streaming=False)

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return round((input_tokens * self.input_rate + output_tokens * self.output_rate) / 1_000_000, 8)
