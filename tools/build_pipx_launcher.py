#!/usr/bin/env python3
"""
Build lightweight Jumperless launcher artifacts (PyPI + pipx, no bundled Python).

Outputs under dist/pipx-launcher/:
  macOS/              Jumperless.app
  JumperlessDMG/      DMG staging (app + Jumperless Python/)
  Jumperless-Installer.dmg   (same layout as Scripts/createDMG.sh)
  linux/              Jumperless.desktop, jumperless-launcher, icon
  windows/            Jumperless.exe (Windows build), .bat fallback, icon.ico
"""

from __future__ import annotations

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
OUT = ROOT / "dist" / "pipx-launcher"
BUILD_WORK = ROOT / "build" / "pipx-launcher"


def rm_tree(path: Path) -> None:
    """Remove a directory tree (handles read-only files and flaky network shares)."""
    if not path.exists():
        return

    def onexc(func, p, exc):
        if isinstance(exc, PermissionError) or (
            isinstance(exc, OSError) and getattr(exc, "winerror", None) == 5
        ):
            try:
                os.chmod(p, stat.S_IWRITE)
                func(p)
            except OSError:
                pass
        else:
            raise exc

    try:
        shutil.rmtree(path, onexc=onexc)
    except OSError:
        if sys.platform == "win32":
            subprocess.run(["cmd", "/c", "rd", "/s", "/q", str(path)], check=False)
        if path.exists() and path.is_dir() and any(path.iterdir()):
            print(f"  Warning: could not fully remove {path}", file=sys.stderr)


def read_version() -> str:
    version_file = ROOT / "VERSION"
    if version_file.is_file():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"


def chmod_exec(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def copy_launcher_scripts(dest_resources: Path) -> None:
    for name in ("pipx_bootstrap.py", "run_in_terminal.sh", "run_in_terminal.bat"):
        src = LAUNCHER / name
        shutil.copy2(src, dest_resources / name)
        if name.endswith(".sh") or name.endswith(".py"):
            chmod_exec(dest_resources / name)


def build_macos(version: str) -> Path:
    app = OUT / "macOS" / "Jumperless.app"
    contents = app / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"
    for directory in (macos, resources):
        directory.mkdir(parents=True, exist_ok=True)

    shutil.copy2(ICONS / "icon.icns", resources / "icon.icns")
    copy_launcher_scripts(resources)
    shutil.copy2(LAUNCHER / "run_in_terminal.sh", resources / "run_in_terminal.sh")
    chmod_exec(resources / "run_in_terminal.sh")

    executable = macos / "Jumperless"
    shutil.copy2(LAUNCHER / "macos_app_executable.sh", executable)
    chmod_exec(executable)

    plist = {
        "CFBundleDisplayName": "Jumperless",
        "CFBundleExecutable": "Jumperless",
        "CFBundleIconFile": "icon.icns",
        "CFBundleIdentifier": "org.jumperless.app.pipx",
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


def build_linux(version: str) -> Path:
    dest = OUT / "linux"
    dest.mkdir(parents=True, exist_ok=True)
    res = dest / "resources"
    res.mkdir(exist_ok=True)

    shutil.copy2(ICONS / "icon.png", res / "jumperless.png")
    copy_launcher_scripts(res)

    wrapper = dest / "jumperless-launcher"
    wrapper.write_text(
        f"""#!/usr/bin/env bash
HERE="$(cd "$(dirname "$0")" && pwd)"
exec "$HERE/resources/run_in_terminal.sh" "$HERE/resources/pipx_bootstrap.py"
""",
        encoding="utf-8",
    )
    chmod_exec(wrapper)

    desktop = dest / "Jumperless.desktop"
    desktop.write_text(
        f"""[Desktop Entry]
Type=Application
Name=Jumperless
Comment=Jumperless Wokwi Bridge (installs from PyPI)
Exec={wrapper.resolve()}
Icon={res.resolve() / "jumperless.png"}
Terminal=false
Categories=Development;Electronics;
Version={version}
""",
        encoding="utf-8",
    )

    print(f"  Linux: {dest}")
    return dest


def build_windows(version: str) -> Path:
    dest = OUT / "windows"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ICONS / "icon.ico", dest / "jumperless.ico")
    shutil.copy2(LAUNCHER / "pipx_bootstrap.py", dest / "pipx_bootstrap.py")
    shutil.copy2(LAUNCHER / "run_in_terminal.bat", dest / "run_in_terminal.bat")

    bat = dest / "Jumperless.bat"
    bat.write_text(
        """@echo off
setlocal EnableExtensions
set "HERE=%~dp0"
if exist "%HERE%Jumperless\\Jumperless.exe" (
  start "" "%HERE%Jumperless\\Jumperless.exe"
  exit /b 0
)
if exist "%HERE%Jumperless.exe" (
  start "" "%HERE%Jumperless.exe"
  exit /b 0
)
call "%HERE%run_in_terminal.bat" "%HERE%pipx_bootstrap.py"
""",
        encoding="utf-8",
    )

    build_windows_exe(dest)

    readme = dest / "README.txt"
    readme.write_text(
        f"""Jumperless Windows launcher (v{version})
=====================================

Double-click Jumperless\\Jumperless.exe (or Jumperless.bat) to:
  1. Ensure Python 3.8+ is installed
  2. Install pipx if needed
  3. Install or upgrade jumperless from PyPI
  4. Start the Jumperless CLI in Windows Terminal

Build Jumperless.exe on Windows: ./tools/build-pipx-launcher.sh
""",
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
        print("  Installing PyInstaller for Windows .exe…")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller>=6.15"],
            check=True,
        )

    work = BUILD_WORK
    rm_tree(work)
    work.mkdir(parents=True, exist_ok=True)

    # Avoid collecting the wrong python3XX.dll from PYTHONPATH (common on 3.14).
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "--distpath",
            str(dest),
            "--workpath",
            str(work),
            str(LAUNCHER / "JumperlessLauncher.spec"),
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )

    # onedir layout: windows/Jumperless/Jumperless.exe + _internal/ (keep together)
    app_dir = dest / "Jumperless"
    exe = app_dir / "Jumperless.exe"
    if exe.is_file():
        print(f"  Windows .exe: {exe}")
        print("  Ship the whole Jumperless/ folder (_internal must stay beside the .exe).")
    else:
        flat = dest / "Jumperless.exe"
        if flat.is_file():
            print(f"  Windows .exe: {flat}")
        else:
            print("  Warning: PyInstaller finished but Jumperless.exe not found", file=sys.stderr)


def create_macos_dmg(macos_app: Path) -> None:
    """Stage app + Jumperless Python and run Scripts/createDMG.sh (full installer layout)."""
    if sys.platform != "darwin":
        return
    if not shutil.which("create-dmg"):
        print("  (skip DMG — install create-dmg, e.g. brew install create-dmg)")
        return

    staging = OUT / "JumperlessDMG"
    dmg_path = OUT / "Jumperless-Installer.dmg"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    shutil.copytree(macos_app, staging / "Jumperless.app")

    populate = ROOT / "Scripts" / "populate_jumperless_python.py"
    python_folder = staging / "Jumperless Python"
    subprocess.run(
        [sys.executable, str(populate), str(python_folder)],
        cwd=ROOT,
        check=True,
    )

    create_script = ROOT / "Scripts" / "createDMG.sh"
    env = os.environ.copy()
    env["JUMPERLESS_DMG_STAGING"] = str(staging)
    env["JUMPERLESS_DMG_OUTPUT"] = str(dmg_path)
    env.setdefault("SKIP_DMG_CODESIGN", "1")

    print(f"  DMG staging: {staging}")
    subprocess.run(["bash", str(create_script)], cwd=ROOT, env=env, check=True)
    print(f"  DMG: {dmg_path}")


def clean_outputs() -> None:
    """Remove only artifacts we are about to rebuild (never wipe unrelated platforms)."""
    if sys.platform == "darwin":
        for path in (
            OUT / "macOS",
            OUT / "linux",
            OUT / "windows",
            OUT / "JumperlessDMG",
            OUT / "Jumperless-Installer.dmg",
        ):
            rm_tree(path)
    elif sys.platform == "win32":
        rm_tree(OUT / "windows")
        rm_tree(BUILD_WORK)
    else:
        rm_tree(OUT / "linux")
        rm_tree(OUT / "windows")


def main() -> int:
    if sys.platform == "win32":
        if not (ICONS / "icon.ico").is_file():
            print(f"Missing Windows icon: {ICONS / 'icon.ico'}", file=sys.stderr)
            return 1
    elif not (ICONS / "icon.icns").is_file():
        print(f"Missing icons under {ICONS}", file=sys.stderr)
        return 1

    version = read_version()
    OUT.mkdir(parents=True, exist_ok=True)
    clean_outputs()

    print(f"Building pipx launcher artifacts (v{version})…")
    if sys.platform == "darwin":
        mac_app = build_macos(version)
        build_linux(version)
        build_windows(version)
        create_macos_dmg(mac_app)
    elif sys.platform == "win32":
        build_windows(version)
    else:
        build_linux(version)
        build_windows(version)

    print()
    print(f"Done → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
