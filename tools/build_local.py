#!/usr/bin/env python3
"""
Build Jumperless native artifacts locally for testing.

Mirrors the CI build steps but writes into a dedicated, git-ignored
`local-builds/` folder (never the CI `builds/` dir), and skips signing.

  macOS    -> local-builds/macos/Jumperless.app + Jumperless-Installer.dmg (unsigned)
  Windows  -> local-builds/windows/Jumperless.exe
  Linux    -> local-builds/linux/Jumperless (+ AppImage if appimagetool is found)
  launcher -> local-builds/launcher/<platform> bundles

Usage:
  python tools/build_local.py                # current platform app + launcher
  python tools/build_local.py --no-launcher  # skip the uv launcher bundle
  python tools/build_local.py --launcher-only
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / "local-builds"
ICONS = ROOT / "assets" / "icons"
PY = sys.executable


def run(cmd: list[str], **kw) -> None:
    print("  $", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, cwd=ROOT, check=True, **kw)


def pyinstaller_onefile(out_subdir: str, icon: Path) -> Path:
    """Build a onefile console executable into local-builds/<out_subdir>."""
    dest = LOCAL / out_subdir
    work = ROOT / "build" / f"local-{out_subdir}"
    dist = ROOT / "dist" / f"local-{out_subdir}"
    cmd = [
        PY, "-m", "PyInstaller", "--clean", "--noconfirm",
        "--onefile", "--console",
        "--name", "Jumperless",
        "--distpath", str(dist),
        "--workpath", str(work),
        "--add-data", f"{ROOT / 'VERSION'}{os.pathsep}.",
        "--exclude-module", "brotli", "--exclude-module", "brotlicffi",
    ]
    if icon.is_file():
        cmd += ["--icon", str(icon)]
    if sys.platform == "win32":
        version_info = ROOT / "version_info.txt"
        run([PY, "Scripts/create_version_info.py"])
        if version_info.is_file():
            cmd += ["--version-file", str(version_info)]
    cmd.append(str(ROOT / "JumperlessWokwiBridge.py"))
    run(cmd)

    dest.mkdir(parents=True, exist_ok=True)
    exe = dist / ("Jumperless.exe" if sys.platform == "win32" else "Jumperless")
    target = dest / exe.name
    shutil.copy2(exe, target)
    if sys.platform != "win32":
        os.chmod(target, 0o755)
    print(f"  -> {target}")
    return target


def build_macos() -> None:
    print("== macOS app + DMG (unsigned) ==")
    env = os.environ.copy()
    env["JUMPERLESS_OUTPUT_DIR"] = str(LOCAL / "macos")
    env["SKIP_DMG_CODESIGN"] = "1"
    subprocess.run(
        ["bash", str(ROOT / "tools" / "build-macos-installer.sh"), "--skip-dmg-codesign"],
        cwd=ROOT, check=True, env=env,
    )


def build_linux() -> None:
    print("== Linux executable ==")
    exe = pyinstaller_onefile("linux", ICONS / "icon.png")
    appimagetool = shutil.which("appimagetool")
    if not appimagetool:
        print("  (appimagetool not found - skipping AppImage; raw executable built)")
        return
    print("  appimagetool found - building AppImage")
    appdir = LOCAL / "linux" / "Jumperless.AppDir"
    if appdir.exists():
        shutil.rmtree(appdir)
    (appdir / "usr" / "bin").mkdir(parents=True)
    shutil.copy2(exe, appdir / "usr" / "bin" / "Jumperless")
    os.chmod(appdir / "usr" / "bin" / "Jumperless", 0o755)
    shutil.copy2(ICONS / "icon.png", appdir / "jumperless.png")
    (appdir / "jumperless.desktop").write_text(
        "[Desktop Entry]\nType=Application\nName=Jumperless\n"
        "Exec=Jumperless\nIcon=jumperless\nCategories=Development;Electronics;\n",
        encoding="utf-8",
    )
    apprun = appdir / "AppRun"
    apprun.write_text(
        '#!/bin/bash\nHERE="$(dirname "$(readlink -f "$0")")"\n'
        'exec "$HERE/usr/bin/Jumperless" "$@"\n',
        encoding="utf-8",
    )
    os.chmod(apprun, 0o755)
    run([appimagetool, str(appdir), str(LOCAL / "linux" / "Jumperless-x86_64.AppImage")])


def build_windows() -> None:
    print("== Windows executable ==")
    pyinstaller_onefile("windows", ICONS / "icon.ico")


def build_launcher() -> None:
    print("== uv backup launcher ==")
    run([PY, "tools/build_launcher.py", "--output-dir", str(LOCAL / "launcher")])


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Jumperless locally into local-builds/")
    parser.add_argument("--no-launcher", action="store_true", help="Skip the uv launcher bundle")
    parser.add_argument("--launcher-only", action="store_true", help="Only build the uv launcher")
    args = parser.parse_args()

    LOCAL.mkdir(parents=True, exist_ok=True)

    if not args.launcher_only:
        if sys.platform == "darwin":
            build_macos()
        elif sys.platform == "win32":
            build_windows()
        else:
            build_linux()

    if not args.no_launcher:
        build_launcher()

    print(f"\nLocal artifacts in {LOCAL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
