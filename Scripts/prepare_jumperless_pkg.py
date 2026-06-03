#!/usr/bin/env python3
"""Ensure jumperless_pkg exists for CI/build (sync bridge.py from canonical script)."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "jumperless_pkg"
REQUIRED = ("__init__.py", "cli.py", "_version.py")


def main() -> int:
    PKG.mkdir(exist_ok=True)

    missing = [name for name in REQUIRED if not (PKG / name).is_file()]
    if missing:
        print(
            "ERROR: jumperless_pkg is incomplete. Missing:",
            ", ".join(missing),
            file=sys.stderr,
        )
        print(
            "Commit jumperless_pkg/ package files (bridge.py is generated here).",
            file=sys.stderr,
        )
        return 1

    src = ROOT / "JumperlessWokwiBridge.py"
    if not src.is_file():
        print(f"ERROR: {src} not found", file=sys.stderr)
        return 1

    shutil.copy2(src, PKG / "bridge.py")
    print(f"Synced {src.name} -> jumperless_pkg/bridge.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
