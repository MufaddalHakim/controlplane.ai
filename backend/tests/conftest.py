from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DATABASE_URL", f"sqlite:///{(ROOT / 'test_controlplane.db').as_posix()}")
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("AUDIT_STORE_RAW", "false")

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
