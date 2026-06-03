#!/usr/bin/env python3
"""
Bootstrap and run Jumperless from PyPI via pipx.

Used by the lightweight cross-platform launcher app (no bundled Python).
Ensures: Python 3.8+ → pipx → latest jumperless on PyPI → run CLI.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys

from pipx_paths import pipx_app_executable, pipx_home

PACKAGE = "jumperless"
MIN_PYTHON = (3, 8)

# Hide console flashes for pip/pipx probes (Windows only).
_WIN_CREATE_NO_WINDOW = 0x08000000


def subprocess_kwargs(*, inherit_console: bool = False) -> dict:
    if sys.platform != "win32" or inherit_console:
        return {}
    return {"creationflags": _WIN_CREATE_NO_WINDOW}


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def parse_version(text: str) -> tuple[int, ...] | None:
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text)
    if not match:
        return None
    parts = [int(match.group(1)), int(match.group(2))]
    if match.group(3) is not None:
        parts.append(int(match.group(3)))
    return tuple(parts)


def python_version_ok(exe: str) -> bool:
    try:
        out = subprocess.run(
            [exe, "-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            **subprocess_kwargs(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if out.returncode != 0:
        return False
    ver = parse_version((out.stdout or "").strip())
    return ver is not None and ver >= MIN_PYTHON


def find_python() -> str | None:
    """Return a Python 3.8+ executable path, or None."""
    seen: set[str] = set()
    candidates: list[str] = []

    if sys.platform == "win32":
        # Prefer the real interpreter behind "py -3" (one probe, not many shims).
        try:
            out = subprocess.run(
                ["py", "-3", "-c", "import sys; print(sys.executable)"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
                **subprocess_kwargs(),
            )
            if out.returncode == 0:
                exe = (out.stdout or "").strip()
                if exe:
                    candidates.append(exe)
        except (OSError, subprocess.TimeoutExpired):
            pass
        for name in ("python3", "python"):
            path = shutil.which(name)
            if path:
                candidates.append(path)
    else:
        for name in ("python3", "python"):
            path = shutil.which(name)
            if path:
                candidates.append(path)
        for path in (
            "/opt/homebrew/bin/python3",
            "/usr/local/bin/python3",
            "/Library/Frameworks/Python.framework/Versions/Current/bin/python3",
            "/usr/bin/python3",
        ):
            if os.path.isfile(path) and os.access(path, os.X_OK):
                candidates.append(path)

    ok: list[str] = []
    for exe in candidates:
        if not exe or exe in seen:
            continue
        seen.add(exe)
        if python_version_ok(exe):
            ok.append(exe)

    if not ok:
        return None
    for exe in ok:
        if module_ok(exe, "pipx"):
            return exe
    return ok[0]


def run(cmd: list[str], *, quiet: bool = True, **kwargs) -> subprocess.CompletedProcess[str]:
    """Run a subprocess. Use quiet=False for pip/pipx install/upgrade (needs a real console on Windows)."""
    eprint("$", " ".join(cmd))
    if "creationflags" not in kwargs and quiet:
        kwargs.update(subprocess_kwargs())
    return subprocess.run(cmd, **kwargs)


def module_ok(py: str, module: str) -> bool:
    r = run([py, "-m", module, "--version"], capture_output=True, text=True)
    return r.returncode == 0


def ensure_pip(py: str) -> None:
    if module_ok(py, "pip"):
        return
    eprint("Installing pip…")
    run([py, "-m", "ensurepip", "--upgrade"], check=True, quiet=False)


def ensure_pipx(py: str) -> None:
    if module_ok(py, "pipx"):
        return
    ensure_pip(py)
    eprint("Installing pipx…")
    run([py, "-m", "pip", "install", "--user", "--upgrade", "pipx"], check=True, quiet=False)
    run([py, "-m", "pipx", "ensurepath"], check=False, quiet=False)


def pipx_has_package(py: str, name: str) -> bool:
    if pipx_app_executable() is not None:
        return True
    r = run([py, "-m", "pipx", "list", "--short"], capture_output=True, text=True)
    if r.returncode != 0:
        return False
    installed = {
        line.strip().split()[0]
        for line in (r.stdout or "").replace("\r", "").splitlines()
        if line.strip()
    }
    return name in installed


def ensure_jumperless(py: str) -> None:
    """Install jumperless via pipx if missing. Do not auto-upgrade (crashes many Windows setups)."""
    ensure_pipx(py)
    if pipx_has_package(py, PACKAGE):
        eprint(f"{PACKAGE} is installed.")
        eprint("To update manually: pipx upgrade jumperless")
        return
    eprint(f"Installing {PACKAGE} from PyPI…")
    run([py, "-m", "pipx", "install", PACKAGE], check=True, quiet=False)


def env_with_user_paths() -> dict[str, str]:
    env = os.environ.copy()
    home = os.path.expanduser("~")
    extra: list[str] = []
    if sys.platform == "win32":
        extra.extend(
            [
                os.path.join(home, ".local", "bin"),
                os.path.join(home, "AppData", "Roaming", "Python", "Scripts"),
                os.path.join(home, "AppData", "Local", "Programs", "Python"),
            ]
        )
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("PYTHONIOENCODING", "utf-8")
    else:
        extra.append(os.path.join(home, ".local", "bin"))
    path = env.get("PATH", "")
    for directory in extra:
        if directory and os.path.isdir(directory) and directory not in path:
            path = f"{directory}{os.pathsep}{path}"
    env["PATH"] = path
    return env


def run_jumperless(py: str) -> int:
    """Run the pipx venv app directly (avoids shadowing by launcher Jumperless.exe on PATH)."""
    env = env_with_user_paths()
    app = pipx_app_executable()
    if app is None:
        eprint(f"Starting {PACKAGE} via pipx…")
        cmd = [py, "-m", "pipx", "run", PACKAGE]
    else:
        eprint(f"Starting {app}…")
        cmd = [str(app)]

    os.chdir(os.path.expanduser("~"))
    return subprocess.call(cmd, env=env)


def print_python_help() -> None:
    eprint()
    eprint("Python 3.8 or newer is required.")
    eprint("Install from https://www.python.org/downloads/ then run this launcher again.")
    if sys.platform == "darwin":
        eprint("On macOS you can also: brew install python3")
    elif sys.platform.startswith("linux"):
        eprint("On Linux try: sudo apt install python3 python3-pip  (Debian/Ubuntu)")
    eprint()


def main() -> int:
    print("Jumperless launcher — preparing PyPI install…")
    try:
        os.chdir(os.path.expanduser("~"))
    except OSError:
        pass
    py = find_python()
    if not py:
        print_python_help()
        return 1

    eprint(f"Using Python: {py}")
    try:
        ensure_jumperless(py)
    except subprocess.CalledProcessError as exc:
        eprint(f"\nSetup failed (exit {exc.returncode}). See messages above.")
        return exc.returncode or 1

    return run_jumperless(py)


if __name__ == "__main__":
    raise SystemExit(main())
