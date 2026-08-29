"""Execute the local evaluation suite and write JSON/Markdown artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.analytics.evaluation import run_evaluation  # noqa: E402
from app.db.database import SessionLocal, init_db  # noqa: E402
from app.services.seed import seed_core  # noqa: E402


def main() -> None:
    init_db()
    with SessionLocal() as db:
        seed_core(db)
        report = run_evaluation(db, write_artifacts=True)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
