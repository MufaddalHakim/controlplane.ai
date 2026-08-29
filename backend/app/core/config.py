"""Environment-driven settings with safe demo defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    root_dir: Path = ROOT_DIR
    demo_mode: bool = _as_bool(os.getenv("DEMO_MODE"), True)
    audit_store_raw: bool = _as_bool(os.getenv("AUDIT_STORE_RAW"), False)
    database_url: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{(ROOT_DIR / 'controlplane.db').as_posix()}"
    )
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    openai_base_url: str = os.getenv(
        "OPENAI_COMPATIBLE_BASE_URL", "https://api.openai.com/v1"
    )
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "")
    policy_dir: Path = ROOT_DIR / "config" / "policies"
    pricing_file: Path = ROOT_DIR / "config" / "model_pricing.yaml"
    knowledge_dir: Path = ROOT_DIR / "data" / "knowledge_base"
    confidential_file: Path = ROOT_DIR / "data" / "confidential" / "corpus.json"
    evaluation_file: Path = ROOT_DIR / "data" / "evaluation" / "cases.json"


settings = Settings()
