#!/usr/bin/env python3
"""
Bootstrap and run Jumperless from PyPI via uv (the backup launcher).

Flow on every launch:
  1. Ensure `uv` is available (install it if missing).
  2. If `jumperless` is not installed as a uv tool, `uv tool install jumperless`.
  3. If it is installed, ask the app itself whether it is out of date
     (`jumperless --check-update`) and only `uv tool upgrade jumperless`
     when the app reports `outdated=true`.
  4. Launch the installed `jumperless` CLI.

This file is self-contained (stdlib only) so it can run from a plain Python
interpreter (macOS .app / Linux .desktop) or from the frozen Windows .exe.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

PACKAGE = "jumperless"


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr, flush=True)


def _candidate_bin_dirs() -> list[Path]:
    """Directories where uv installs itself and tool entry points."""
    home = Path.home()
    dirs = [
        home / ".local" / "bin",
        home / ".cargo" / "bin",
    ]
    if os.name == "nt":
        dirs += [
            home / ".local" / "bin",
            Path(os.environ.get("APPDATA", home)) / "uv" / "bin",
        ]
    xdg = os.environ.get("XDG_BIN_HOME")
    if xdg:
        dirs.append(Path(xdg))
    return dirs


def _exe_name(name: str) -> str:
    return f"{name}.exe" if os.name == "nt" else name


def _add_bin_dirs_to_path() -> None:
    parts = os.environ.get("PATH", "").split(os.pathsep)
    for d in _candidate_bin_dirs():
        s = str(d)
        if d.is_dir() and s not in parts:
            parts.insert(0, s)
    os.environ["PATH"] = os.pathsep.join(parts)


def find_executable(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    for d in _candidate_bin_dirs():
        candidate = d / _exe_name(name)
        if candidate.is_file():
            return str(candidate)
    return None


def ensure_uv() -> str | None:
    """Return a path to uv, installing it if necessary."""
    _add_bin_dirs_to_path()
    uv = find_executable("uv")
    if uv:
        return uv

    eprint("uv not found — installing it…")
    try:
        if os.name == "nt":
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "ByPass",
                    "-Command",
                    "irm https://astral.sh/uv/install.ps1 | iex",
                ],
                check=True,
            )
        elif shutil.which("curl"):
            subprocess.run(
                "curl -LsSf https://astral.sh/uv/install.sh | sh",
                shell=True,
                check=True,
            )
        elif shutil.which("wget"):
            subprocess.run(
                "wget -qO- https://astral.sh/uv/install.sh | sh",
                shell=True,
                check=True,
            )
        else:
            raise FileNotFoundError("no curl/wget")
    except Exception as exc:  # noqa: BLE001 — fall back to pip
        eprint(f"Official uv installer failed ({exc}); trying pip…")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user", "--upgrade", "uv"],
                check=True,
            )
        except Exception as exc2:  # noqa: BLE001
            eprint(f"Could not install uv: {exc2}")
            return None

    _add_bin_dirs_to_path()
    return find_executable("uv")


def tool_installed(uv: str) -> bool:
    try:
        result = subprocess.run(
            [uv, "tool", "list"],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:  # noqa: BLE001
        return False
    return any(line.strip().startswith(PACKAGE) for line in result.stdout.splitlines())


def app_is_outdated(exe: str) -> bool:
    """Ask the installed app whether a newer PyPI release exists.

    The app prints a line like `current=1.2.3 latest=1.2.4 outdated=true`.
    Returns False (do not upgrade) when the check is inconclusive.
    """
    try:
        result = subprocess.run(
            [exe, "--check-update"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        eprint(f"Update check failed ({exc}); skipping upgrade.")
        return False

    for line in (result.stdout + result.stderr).splitlines():
        token = line.strip().lower()
        if "outdated=" in token:
            return "outdated=true" in token
    return False


def ensure_jumperless(uv: str) -> None:
    if not tool_installed(uv):
        eprint(f"Installing {PACKAGE} from PyPI via uv…")
        subprocess.run([uv, "tool", "install", PACKAGE], check=True)
        _add_bin_dirs_to_path()
        return

    exe = find_executable(PACKAGE)
    if exe and app_is_outdated(exe):
        eprint(f"A newer {PACKAGE} is available — upgrading…")
        subprocess.run([uv, "tool", "upgrade", PACKAGE], check=False)
    else:
        eprint(f"{PACKAGE} is up to date.")


def launch(uv: str) -> int:
    _add_bin_dirs_to_path()
    os.chdir(os.path.expanduser("~"))
    exe = find_executable(PACKAGE)
    cmd = [exe] if exe else [uv, "tool", "run", PACKAGE]
    eprint(f"Starting {PACKAGE}…")
    return subprocess.call(cmd)


def main() -> int:
    print("Jumperless launcher — preparing PyPI install via uv…")
    uv = ensure_uv()
    if not uv:
        eprint("")
        eprint("Could not find or install uv. Install it manually:")
        eprint("  https://docs.astral.sh/uv/getting-started/installation/")
        eprint("then run:  uv tool install jumperless && jumperless")
        try:
            input("\nPress Enter to close…")
        except EOFError:
            pass
        return 1

    try:
        ensure_jumperless(uv)
    except subprocess.CalledProcessError as exc:
        eprint(f"Install failed: {exc}")
        try:
            input("\nPress Enter to close…")
        except EOFError:
            pass
        return 1

    return launch(uv)


if __name__ == "__main__":
    raise SystemExit(main())
