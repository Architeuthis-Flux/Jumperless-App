"""Read the app version from the repo-root VERSION file."""

from __future__ import annotations

import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def read_version(default: str = "0.0.0") -> str:
    """Return the release version from VERSION (PyPI metadata as fallback)."""
    scripts = _repo_root() / "Scripts"
    if scripts.is_dir():
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        try:
            from read_version import read_version as _read

            return _read(default)
        except ImportError:
            pass

    candidates: list[Path] = [_repo_root() / "VERSION"]

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
