# Jumperless-App

An app to talk to your Jumperless V5 — connect to Wokwi, flash Arduino sketches,
update firmware, and drive the board from a CLI.

## Install

The recommended way is from PyPI:

```bash
pip install jumperless        # or: uv tool install jumperless
jumperless
```

Prefer an icon? Grab a native build (Windows `.exe`, macOS `.dmg`,
Linux `.AppImage`) or the backup launcher from the
[latest release](https://github.com/Architeuthis-Flux/JumperlessV5/releases/latest).

## Run from source

```bash
python -m pip install -r requirements.txt
python JumperlessWokwiBridge.py
```

## Building / releasing

The whole packaging chain (PyPI, native installers, the uv backup launcher, CI,
and local test builds) is documented in [docs/PACKAGING.md](docs/PACKAGING.md).

Quick local build for testing:

```bash
python tools/build_local.py     # builds the current platform into local-builds/
```
