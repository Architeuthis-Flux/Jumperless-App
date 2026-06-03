#!/usr/bin/env python3
"""Read app version from repo-root VERSION (no jumperless_pkg import required)."""

from __future__ import annotations

import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def read_version(default: str = "0.0.0") -> str:
    candidates: list[Path] = [repo_root() / "VERSION"]

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir / "VERSION")
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "VERSION")

    for path in candidates:
        if path.is_file():
            text = path.read_text(encoding="utf-8").strip()
            if text:
                return text

    try:
        from importlib.metadata import version

        return version("jumperless")
    except Exception:
        return default
