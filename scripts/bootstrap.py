"""Create local dependencies for the zero-key prototype."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"


def run(command: list[str], cwd: Path = ROOT) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def main() -> None:
    if not VENV.exists():
        run([sys.executable, "-m", "venv", str(VENV)])
    python = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    run([str(python), "-m", "pip", "install", "-r", str(ROOT / "backend" / "requirements.txt")])
    if not (ROOT / "frontend" / "node_modules").exists():
        run(["npm", "install"], cwd=ROOT / "frontend")
    print("\nBootstrap complete. Next: python scripts/seed_demo.py --reset")


if __name__ == "__main__":
    main()
