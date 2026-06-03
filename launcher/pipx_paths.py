"""Shared pipx install locations for the launcher (no subprocess)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PACKAGE = "jumperless"


def pipx_home() -> Path:
    if os.environ.get("PIPX_HOME"):
        return Path(os.environ["PIPX_HOME"])
    if sys.platform == "win32":
        return Path.home() / "pipx"
    return Path.home() / ".local" / "pipx"


def pipx_app_executable() -> Path | None:
    venv = pipx_home() / "venvs" / PACKAGE
    if sys.platform == "win32":
        candidates = (
            venv / "Scripts" / f"{PACKAGE}.exe",
            venv / "Scripts" / f"{PACKAGE}.EXE",
        )
    else:
        candidates = (venv / "bin" / PACKAGE,)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None
