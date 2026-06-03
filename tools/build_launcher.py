#!/usr/bin/env python3
"""
Build the lightweight Jumperless backup launcher (PyPI + uv, no bundled Python).

The launcher does not contain the app; on first run it uses `uv` to install
`jumperless` from PyPI, self-updates when the app reports it is out of date,
and then starts the CLI. See launcher/uv_bootstrap.py.

Outputs (per build host) under the chosen output dir (default dist/launcher/):
  macOS/Jumperless.app          (Resources/uv_bootstrap.py + terminal wrappers)
  linux/                        Jumperless.desktop + jumperless-launcher + icon
  windows/                      Jumperless/Jumperless.exe (+ .bat fallback, icon)

Output dir precedence: --output-dir  >  $JUMPERLESS_OUTPUT_DIR  >  dist/launcher
"""

from __future__ import annotations

import argparse
import os
import plistlib
import shutil
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAUNCHER = ROOT / "launcher"
ICONS = ROOT / "assets" / "icons"
BUILD_WORK = ROOT / "build" / "launcher"

# Windows CI consoles default to cp1252; keep stdout UTF-8 tolerant.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def resolve_out(arg_out: str | None) -> Path:
    base = arg_out or os.environ.get("JUMPERLESS_OUTPUT_DIR")
    if base:
        return Path(base).resolve()
    return ROOT / "dist" / "launcher"


def read_version() -> str:
    version_file = ROOT / "VERSION"
    if version_file.is_file():
        return version_file.read_text(encoding="utf-8").strip() or "0.0.0"
    return "0.0.0"


def chmod_exec(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def copy_shared(dest: Path) -> None:
    """Copy the bootstrap + terminal wrappers into a resources dir."""
    for name in ("uv_bootstrap.py", "run_in_terminal.sh", "run_in_terminal.bat"):
        src = LAUNCHER / name
        if src.is_file():
            shutil.copy2(src, dest / name)
            if name.endswith((".sh", ".py")):
                chmod_exec(dest / name)


def build_macos(out: Path, version: str) -> Path:
    app = out / "macOS" / "Jumperless.app"
    contents = app / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"
    for directory in (macos, resources):
        directory.mkdir(parents=True, exist_ok=True)

    shutil.copy2(ICONS / "icon.icns", resources / "icon.icns")
    copy_shared(resources)

    executable = macos / "Jumperless"
    shutil.copy2(LAUNCHER / "macos_app_executable.sh", executable)
    chmod_exec(executable)

    plist = {
        "CFBundleDisplayName": "Jumperless",
        "CFBundleExecutable": "Jumperless",
        "CFBundleIconFile": "icon.icns",
        "CFBundleIdentifier": "org.jumperless.app.launcher",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "Jumperless",
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": version,
        "CFBundleVersion": version,
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "10.13",
    }
    with (contents / "Info.plist").open("wb") as handle:
        plistlib.dump(plist, handle)

    print(f"  macOS: {app}")
    return app


def build_linux(out: Path, version: str) -> Path:
    dest = out / "linux"
    res = dest / "resources"
    res.mkdir(parents=True, exist_ok=True)

    shutil.copy2(ICONS / "icon.png", res / "jumperless.png")
    copy_shared(res)

    wrapper = dest / "jumperless-launcher"
    wrapper.write_text(
        '#!/usr/bin/env bash\n'
        'HERE="$(cd "$(dirname "$0")" && pwd)"\n'
        'exec "$HERE/resources/run_in_terminal.sh" "$HERE/resources/uv_bootstrap.py"\n',
        encoding="utf-8",
    )
    chmod_exec(wrapper)

    desktop = dest / "Jumperless.desktop"
    desktop.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Jumperless\n"
        "Comment=Jumperless Wokwi Bridge (installs from PyPI via uv)\n"
        f"Exec={wrapper.resolve()}\n"
        f"Icon={(res / 'jumperless.png').resolve()}\n"
        "Terminal=false\n"
        "Categories=Development;Electronics;\n"
        f"Version={version}\n",
        encoding="utf-8",
    )

    print(f"  Linux: {dest}")
    return dest


def build_windows(out: Path, version: str) -> Path:
    dest = out / "windows"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ICONS / "icon.ico", dest / "jumperless.ico")
    shutil.copy2(LAUNCHER / "uv_bootstrap.py", dest / "uv_bootstrap.py")
    shutil.copy2(LAUNCHER / "run_in_terminal.bat", dest / "run_in_terminal.bat")

    bat = dest / "Jumperless.bat"
    bat.write_text(
        "@echo off\r\n"
        "setlocal EnableExtensions\r\n"
        'set "HERE=%~dp0"\r\n'
        'if exist "%HERE%Jumperless\\Jumperless.exe" (\r\n'
        '  start "" "%HERE%Jumperless\\Jumperless.exe"\r\n'
        "  exit /b 0\r\n"
        ")\r\n"
        'call "%HERE%run_in_terminal.bat" "%HERE%uv_bootstrap.py"\r\n',
        encoding="utf-8",
    )

    build_windows_exe(dest)

    (dest / "README.txt").write_text(
        f"Jumperless Windows launcher (v{version})\r\n"
        "=====================================\r\n\r\n"
        "Double-click Jumperless\\Jumperless.exe (or Jumperless.bat) to:\r\n"
        "  1. Ensure uv is installed\r\n"
        "  2. Install or upgrade jumperless from PyPI via uv\r\n"
        "  3. Start the Jumperless CLI\r\n",
        encoding="utf-8",
    )

    print(f"  Windows: {dest}")
    return dest


def build_windows_exe(dest: Path) -> None:
    """Build Jumperless.exe with PyInstaller onedir (Windows host only)."""
    if sys.platform != "win32":
        print("  Windows .exe: run this build on Windows to produce Jumperless.exe")
        return

    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("  Installing PyInstaller for Windows .exe...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller>=6.15"],
            check=True,
        )

    work = BUILD_WORK
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.pop("PYTHONPATH", None)  # avoid grabbing the wrong python3XX.dll

    subprocess.run(
        [
            sys.executable, "-m", "PyInstaller",
            "--clean", "--noconfirm",
            "--distpath", str(dest),
            "--workpath", str(work),
            str(LAUNCHER / "JumperlessLauncher.spec"),
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )

    exe = dest / "Jumperless" / "Jumperless.exe"
    if exe.is_file():
        print(f"  Windows .exe: {exe} (ship the whole Jumperless/ folder)")
    else:
        print("  Warning: PyInstaller finished but Jumperless.exe not found", file=sys.stderr)


def clean(out: Path) -> None:
    if sys.platform == "darwin":
        targets = [out / "macOS", out / "linux", out / "windows"]
    elif sys.platform == "win32":
        targets = [out / "windows"]
    else:
        targets = [out / "linux", out / "windows"]
    for t in targets:
        if t.exists():
            shutil.rmtree(t, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Jumperless uv backup launcher")
    parser.add_argument("--output-dir", help="Where to write the launcher bundles")
    args = parser.parse_args()

    out = resolve_out(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if sys.platform == "win32":
        if not (ICONS / "icon.ico").is_file():
            print(f"Missing Windows icon: {ICONS / 'icon.ico'}", file=sys.stderr)
            return 1
    elif not (ICONS / "icon.icns").is_file():
        print(f"Missing macOS icon: {ICONS / 'icon.icns'}", file=sys.stderr)
        return 1

    version = read_version()
    clean(out)

    print(f"Building uv launcher artifacts (v{version}) -> {out}")
    if sys.platform == "darwin":
        build_macos(out, version)
        build_linux(out, version)
        build_windows(out, version)
    elif sys.platform == "win32":
        build_windows(out, version)
    else:
        build_linux(out, version)
        build_windows(out, version)

    print(f"Done -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
