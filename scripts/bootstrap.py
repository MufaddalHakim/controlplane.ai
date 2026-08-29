"""Create local dependencies for the zero-key prototype."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"
MINIMUM_PYTHON = (3, 11)


def run(command: list[str], cwd: Path = ROOT) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def ensure_virtualenv() -> Path:
    """Create the project virtualenv and reject stale, non-portable environments."""
    if not VENV.exists():
        run([sys.executable, "-m", "venv", str(VENV)])
    python = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    probe = subprocess.run(
        [str(python), "--version"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        raise SystemExit(
            "The existing .venv is not usable on this machine. Remove the .venv "
            "directory and run scripts/bootstrap.py again; virtual environments "
            "must not be copied between machines."
        )
    return python


def main() -> None:
    if sys.version_info < MINIMUM_PYTHON:
        required = ".".join(map(str, MINIMUM_PYTHON))
        current = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        raise SystemExit(f"ControlPlane.ai requires Python {required}+; found {current}.")
    python = ensure_virtualenv()
    run([str(python), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")])
    if not (ROOT / "frontend" / "node_modules").exists():
        run(["npm", "ci"], cwd=ROOT / "frontend")
    seed_command = (
        r".\.venv\Scripts\python.exe scripts\seed_demo.py --reset"
        if os.name == "nt"
        else ".venv/bin/python scripts/seed_demo.py --reset"
    )
    print(f"\nBootstrap complete. Next: {seed_command}")


if __name__ == "__main__":
    main()
