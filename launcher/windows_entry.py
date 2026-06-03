#!/usr/bin/env python3
"""
Windows double-click entry for the PyPI/pipx launcher.

If jumperless is already installed via pipx, open it directly in Windows Terminal.
Otherwise run pipx_bootstrap.py once to install, then start the app.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from pipx_paths import pipx_app_executable

_CREATE_NO_WINDOW = 0x08000000
_CREATE_NEW_CONSOLE = 0x00000010


def base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def bootstrap_script() -> Path:
    return base_dir() / "pipx_bootstrap.py"


def resolve_python_command(bootstrap: Path) -> list[str]:
    if shutil.which("py"):
        try:
            out = subprocess.run(
                ["py", "-3", "-c", "import sys; print(sys.executable)"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
                creationflags=_CREATE_NO_WINDOW,
            )
            if out.returncode == 0:
                exe = (out.stdout or "").strip()
                if exe:
                    return [exe, str(bootstrap)]
        except (OSError, subprocess.TimeoutExpired):
            pass
    for name in ("python3", "python"):
        path = shutil.which(name)
        if path:
            return [path, str(bootstrap)]
    return ["python", str(bootstrap)]


def launch_command() -> list[str] | None:
    app = pipx_app_executable()
    if app is not None:
        return [str(app)]
    bootstrap = bootstrap_script()
    if not bootstrap.is_file():
        return None
    return resolve_python_command(bootstrap)


def show_error(message: str) -> None:
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, "Jumperless", 0x10)
    except Exception:
        print(message, file=sys.stderr)


def open_in_terminal(command: list[str]) -> int:
    home = os.path.expanduser("~")
    wt = shutil.which("wt")
    if wt:
        subprocess.Popen(
            [
                wt,
                "-w",
                "0",
                "-d",
                home,
                "nt",
                "--hold",
                "--title",
                "Jumperless",
                "--",
                *command,
            ],
            creationflags=subprocess.DETACHED_PROCESS,
            close_fds=True,
        )
        return 0

    subprocess.Popen(
        command,
        cwd=home,
        creationflags=_CREATE_NEW_CONSOLE,
        close_fds=True,
    )
    return 0


def launch_in_terminal() -> int:
    command = launch_command()
    if command is None:
        show_error(
            "Launcher files are incomplete.\n"
            f"Missing bootstrap: {bootstrap_script()}"
        )
        return 1
    return open_in_terminal(command)


def main() -> int:
    return launch_in_terminal()


if __name__ == "__main__":
    raise SystemExit(main())
