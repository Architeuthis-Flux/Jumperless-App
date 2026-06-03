#!/usr/bin/env python3
"""Read VERSION and patch macOS bundle Info.plist."""

from __future__ import annotations

import plistlib
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from read_version import read_version as get_app_version  # noqa: E402


def find_macos_app_bundle(root: Path | None = None) -> Path | None:
    """Locate a built Jumperless.app under dist/."""
    root = (root or Path.cwd()).resolve()
    candidates = (
        root / "dist" / "Jumperless.app",
        root / "dist" / "macos" / "Jumperless.app",
    )
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "Contents" / "Info.plist").is_file():
            return candidate
    return None


def patch_macos_app_plist(app_bundle: Path, version: str | None = None, root: Path | None = None) -> str:
    """Set CFBundleShortVersionString and CFBundleVersion on a .app bundle."""
    app_bundle = app_bundle.resolve()
    plist_path = app_bundle / "Contents" / "Info.plist"
    if not plist_path.is_file():
        raise FileNotFoundError(f"Info.plist not found: {plist_path}")

    version = version or get_app_version()
    with plist_path.open("rb") as handle:
        plist = plistlib.load(handle)

    plist["CFBundleShortVersionString"] = version
    plist["CFBundleVersion"] = version

    with plist_path.open("wb") as handle:
        plistlib.dump(plist, handle)

    return version


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Patch Jumperless.app Info.plist version")
    parser.add_argument(
        "app_bundle",
        nargs="?",
        help="Path to Jumperless.app (default: search under dist/)",
    )
    parser.add_argument("--version", help="Override version string")
    parser.add_argument("--print-version", action="store_true", help="Print version and exit")
    args = parser.parse_args()

    root = Path.cwd()
    if args.print_version:
        print(get_app_version())
        return 0

    app_bundle = Path(args.app_bundle) if args.app_bundle else find_macos_app_bundle(root)
    if app_bundle is None:
        print("ERROR: Jumperless.app not found under dist/", flush=True)
        return 1

    version = patch_macos_app_plist(app_bundle, args.version)
    print(f"Set {app_bundle.name} version to {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
