# Universal macOS Build - Quick Start

Building a universal macOS app (Intel + Apple Silicon)? Here's what you need:

## TL;DR

```bash
./tools/build-macos-installer.sh
```

That script: creates `venv-packager/` with a universal python.org interpreter, installs deps, runs PyInstaller, and writes `Jumperless_Installer.dmg`.

Manual steps:

```bash
# 1. Create a universal python.org venv (one-time setup)
./Scripts/setup_universal_python.sh

# 2. Build app + DMG
venv-packager/bin/python JumperlessAppPackagerOriginalAllPlatforms.py --macos-installer
```

## Why a special Python?

**Universal2 PyInstaller builds require a fat Python interpreter** (x86_64 + arm64). Micromamba, Homebrew, and pyenv builds on Apple Silicon are usually arm64-only and cannot produce Intel + Apple Silicon apps.

The setup script uses a **python.org universal framework** build. If you already have one installed (check with `ls /Library/Frameworks/Python.framework/Versions/`), it reuses it — you may already have 3.12 universal without realizing it.

If none is found, it downloads and installs **Python 3.11.9** (matches CI).

## What the setup script does

1. Finds or installs a universal python.org interpreter
2. Creates `venv-packager/` in the repo root
3. Installs packager + universal native deps (`psutil`, `pyserial`, …)

Verify your venv is universal:

```bash
lipo -info venv-packager/bin/python3
# Architectures in the fat file: ... are: x86_64 arm64
```

## Dependency install only

If you already have `venv-packager` and only need to refresh deps:

```bash
source venv-packager/bin/activate
./Scripts/install_universal_deps.sh
```

## Troubleshooting

**Packager says arm64-only / PyInstaller architecture errors**
→ You are not using the packager venv. Run `./Scripts/setup_universal_python.sh` and activate `venv-packager`.

**"Some dependencies are not universal binaries!"**
→ `./Scripts/install_universal_deps.sh` (inside `venv-packager`)

**Want to pin a specific interpreter**
→ `JUMPERLESS_PYTHON=/path/to/python3 ./Scripts/setup_universal_python.sh`

## More details

See `BridgeDocs/UNIVERSAL_MACOS_BUILD.md` for CI integration and architecture notes.
