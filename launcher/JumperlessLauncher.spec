# PyInstaller spec: thin Windows launcher (.exe) for the uv/PyPI bootstrap.
# Uses onedir (not onefile) so python3XX.dll is loaded reliably on Windows,
# and console=True so double-clicking opens a terminal for the CLI.
#
# Build (on Windows):
#   python -m PyInstaller --clean --noconfirm launcher/JumperlessLauncher.spec

import pathlib
import sys

LAUNCHER = pathlib.Path(SPECPATH).resolve()
ROOT = LAUNCHER.parent

# Python DLLs must come from the same install as the build interpreter.
_python_home = pathlib.Path(sys._base_executable).resolve().parent
_binaries = []
for _dll_name in ("python3.dll", f"python{sys.version_info.major}{sys.version_info.minor}.dll"):
    _dll_path = _python_home / _dll_name
    if _dll_path.is_file():
        _binaries.append((str(_dll_path), "."))

a = Analysis(
    [str(LAUNCHER / "uv_bootstrap.py")],
    pathex=[str(LAUNCHER)],
    binaries=_binaries,
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Jumperless",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "assets" / "icons" / "icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Jumperless",
)
