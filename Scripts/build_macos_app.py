#!/usr/bin/env python3
"""Build dist/Jumperless.app with PyInstaller (universal2 when possible).

Replaces the old monolithic packager's macOS path. Steps:
  1. PyInstaller windowed .app from JumperlessWokwiBridge.py (bundles VERSION).
  2. Patch Info.plist version via Scripts/app_version.py.
  3. Install the Terminal launcher: rename the real binary to Jumperless_cli and
     drop Scripts/jumperless_cli_launcher.sh in as the bundle's main executable,
     so double-clicking the .app opens Terminal and runs the CLI.

Run with the universal python.org interpreter (venv-packager) for a fat binary.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "Scripts"
APP = ROOT / "dist" / "Jumperless.app"
MACOS_DIR = APP / "Contents" / "MacOS"
ICON = ROOT / "assets" / "icons" / "icon.icns"
CLI_LAUNCHER = SCRIPTS / "jumperless_cli_launcher.sh"


def interpreter_is_universal() -> bool:
    try:
        out = subprocess.run(
            ["lipo", "-info", sys.executable],
            capture_output=True, text=True, check=False,
        ).stdout
    except FileNotFoundError:
        return False
    return "x86_64" in out and "arm64" in out


def build(target_arch: str) -> None:
    print(f"=== PyInstaller (.app, target-arch={target_arch}) ===")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "-y", "--console", "--windowed",
        "--name", "Jumperless",
        "--target-arch", target_arch,
        "--exclude-module", "brotli",
        "--exclude-module", "brotlicffi",
        "--add-data", f"{ROOT / 'VERSION'}{os.pathsep}.",
    ]
    if ICON.is_file():
        cmd += ["--icon", str(ICON)]
    cmd.append(str(ROOT / "JumperlessWokwiBridge.py"))
    subprocess.run(cmd, cwd=ROOT, check=True)

    if not APP.is_dir():
        raise SystemExit(f"PyInstaller did not produce {APP}")


def patch_version() -> None:
    version_script = SCRIPTS / "app_version.py"
    if version_script.is_file():
        print("=== Patching Info.plist version ===")
        subprocess.run([sys.executable, str(version_script), str(APP)], cwd=ROOT, check=True)


def install_launcher() -> None:
    print("=== Installing Terminal launcher into bundle ===")
    real = MACOS_DIR / "Jumperless"
    cli = MACOS_DIR / "Jumperless_cli"
    if not real.is_file():
        raise SystemExit(f"Built executable not found: {real}")
    if not CLI_LAUNCHER.is_file():
        raise SystemExit(f"Launcher script not found: {CLI_LAUNCHER}")
    if cli.exists():
        cli.unlink()
    real.rename(cli)
    os.chmod(cli, 0o755)
    shutil.copy2(CLI_LAUNCHER, real)
    os.chmod(real, 0o755)
    print(f"  {real.name} -> launcher, real binary -> {cli.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Jumperless.app")
    parser.add_argument(
        "--target-arch",
        choices=["universal2", "arm64", "x86_64"],
        default=None,
        help="PyInstaller target arch (default: universal2 if interpreter is fat, else native)",
    )
    args = parser.parse_args()

    target_arch = args.target_arch or ("universal2" if interpreter_is_universal() else "arm64")
    build(target_arch)
    patch_version()
    install_launcher()
    print(f"\nBuilt {APP}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
