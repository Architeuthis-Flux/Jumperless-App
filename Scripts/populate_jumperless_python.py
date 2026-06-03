#!/usr/bin/env python3
"""Populate a Jumperless Python fallback folder from current repo sources."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from read_version import read_version  # noqa: E402


def populate_jumperless_python_folder(dest: Path, root: Path | None = None) -> Path:
    """Copy the latest script, VERSION, requirements, launcher, and assets into dest."""
    root = (root or ROOT).resolve()
    dest = dest.resolve()

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    file_copies = (
        ("JumperlessWokwiBridge.py", "JumperlessWokwiBridge.py"),
        ("VERSION", "VERSION"),
        ("requirements.txt", "requirements.txt"),
        ("Scripts/jumperless_launcher.sh", "jumperless_launcher.sh"),
    )
    for src_rel, dst_name in file_copies:
        src = root / src_rel
        dst = dest / dst_name
        if src.is_file():
            shutil.copy2(src, dst)
            if dst_name.endswith(".sh"):
                os.chmod(dst, 0o755)
            print(f"Copied {src_rel} -> {dest.name}/{dst_name}")
        else:
            print(f"Warning: missing {src_rel}")

    assets_src = root / "assets"
    if assets_src.is_dir():
        shutil.copytree(assets_src, dest / "assets", dirs_exist_ok=True)
        print(f"Copied assets/ -> {dest.name}/assets")

    version = read_version()
    print(f"Jumperless Python folder ready at {dest} (version {version})")
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description="Populate Jumperless Python fallback folder")
    parser.add_argument(
        "dest",
        nargs="?",
        default="Jumperless Python",
        help="Destination folder (default: Jumperless Python)",
    )
    args = parser.parse_args()
    populate_jumperless_python_folder(Path(args.dest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
