#!/usr/bin/env bash
# End-to-end macOS release build:
#   1. Universal python.org venv (venv-packager/)
#   2. Packager + app dependencies (universal fat binaries)
#   3. PyInstaller .app (Intel + Apple Silicon when Python is universal)
#   4. Polished installer DMG
#
# Usage:
#   ./tools/build-macos-installer.sh              # full pipeline (local)
#   ./tools/build-macos-installer.sh --ci         # GitHub Actions (paths + zip artifact)
#   ./tools/build-macos-installer.sh --fresh      # recreate venv from scratch
#   ./tools/build-macos-installer.sh --skip-setup # app + dmg only (venv must exist)
#   ./tools/build-macos-installer.sh --skip-dmg-codesign
#
# Output (local):
#   Jumperless_Installer.dmg
#   dist/Jumperless.app
#
# Output (--ci):
#   builds/Jumperless-Installer.dmg
#   builds/Jumperless-macOS-Apple-Silicon.zip
#   dist/macos/Jumperless.app

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VENV_DIR="$ROOT/venv-packager"
VENV_PY="$VENV_DIR/bin/python3"
DMG_OUT="$ROOT/Jumperless_Installer.dmg"

FRESH=0
SKIP_SETUP=0
CI=0
DMG_ONLY=0

usage() {
  sed -n '2,22p' "$0"
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ci) CI=1; shift ;;
    --fresh) FRESH=1; shift ;;
    --skip-setup) SKIP_SETUP=1; shift ;;
    --skip-dmg-codesign) export SKIP_DMG_CODESIGN=1; shift ;;
    --dmg-only) DMG_ONLY=1; shift ;;
    -h|--help) usage 0 ;;
    *) echo "Unknown option: $1" >&2; usage 1 ;;
  esac
done

if [[ "$OSTYPE" != darwin* ]]; then
  echo "❌ This script is macOS only." >&2
  exit 1
fi

step() {
  echo ""
  echo "================================"
  echo "$1"
  echo "================================"
}

if [[ "$CI" == "1" ]]; then
  export JUMPERLESS_CI=1
  export JUMPERLESS_NONINTERACTIVE=1
  DMG_OUT="$ROOT/builds/Jumperless-Installer.dmg"
  SKIP_SETUP=0
fi

if [[ "$DMG_ONLY" == "1" ]]; then
  export JUMPERLESS_DMG_OUTPUT="$DMG_OUT"
  chmod +x "$ROOT/Scripts/createDMG.sh" "$ROOT/Scripts/populate_jumperless_python.py"
  step "Refresh Jumperless Python + create installer DMG"
  POPULATE_PY="$ROOT/venv-packager/bin/python3"
  if [[ ! -x "$POPULATE_PY" ]]; then
    POPULATE_PY="$(command -v python3)"
  fi
  "$POPULATE_PY" "$ROOT/Scripts/populate_jumperless_python.py" "$ROOT/Jumperless Python"
  APP_SRC="$ROOT/dist/macos/Jumperless.app"
  if [[ ! -d "$APP_SRC" ]]; then
    APP_SRC="$ROOT/dist/Jumperless.app"
  fi
  if [[ ! -d "$APP_SRC" ]]; then
    echo "❌ No Jumperless.app found under dist/" >&2
    exit 1
  fi
  rm -rf "$ROOT/JumperlessDMG"
  mkdir -p "$ROOT/JumperlessDMG"
  cp -R "$APP_SRC" "$ROOT/JumperlessDMG/Jumperless.app"
  if [[ -d "$ROOT/Jumperless Python" ]]; then
    cp -R "$ROOT/Jumperless Python" "$ROOT/JumperlessDMG/Jumperless Python"
  fi
  bash "$ROOT/Scripts/createDMG.sh"
  echo "DMG: $DMG_OUT"
  exit 0
fi

step "Step 1/4 — Universal Python venv"

chmod +x "$ROOT/Scripts/resolve_universal_python.sh" \
         "$ROOT/Scripts/setup_universal_python.sh" \
         "$ROOT/Scripts/install_universal_deps.sh" \
         "$ROOT/Scripts/createDMG.sh" \
         "$ROOT/tools/createDMG.sh"

if [[ "$SKIP_SETUP" == "1" ]]; then
  if [[ ! -x "$VENV_PY" ]]; then
    echo "❌ --skip-setup but venv-packager not found. Run without --skip-setup first." >&2
    exit 1
  fi
  echo "Skipping venv setup (--skip-setup)"
elif [[ "$CI" == "1" ]]; then
  if [[ -x "$VENV_PY" ]]; then
    echo "CI: reusing cached venv-packager (refreshing deps)"
    export JUMPERLESS_PYTHON="$VENV_PY"
    export JUMPERLESS_KEEP_VENV=1
  else
    echo "CI: creating venv-packager"
    export JUMPERLESS_KEEP_VENV=0
  fi
  "$ROOT/Scripts/setup_universal_python.sh"
elif [[ "$FRESH" == "1" || ! -x "$VENV_PY" ]]; then
  export JUMPERLESS_KEEP_VENV=0
  "$ROOT/Scripts/setup_universal_python.sh"
else
  echo "venv-packager exists — refreshing dependencies"
  export JUMPERLESS_PYTHON="$VENV_PY"
  export JUMPERLESS_KEEP_VENV=1
  "$ROOT/Scripts/setup_universal_python.sh"
fi

if [[ ! -x "$VENV_PY" ]]; then
  echo "❌ Packager venv missing after setup: $VENV_PY" >&2
  exit 1
fi

step "Step 2/4 — Verify universal interpreter"
lipo -info "$VENV_PY"
"$VENV_PY" --version

step "Step 3/4 — Install create-dmg (if needed)"
if ! command -v create-dmg >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    brew install create-dmg
  else
    echo "❌ create-dmg not found and Homebrew is unavailable." >&2
    exit 1
  fi
fi

step "Step 4/4 — Build app + DMG"
export JUMPERLESS_NONINTERACTIVE=1
export JUMPERLESS_DMG_OUTPUT="$DMG_OUT"

if [[ "$CI" == "1" ]]; then
  export JUMPERLESS_SKIP_DMG=1
  "$VENV_PY" "$ROOT/JumperlessAppPackagerOriginalAllPlatforms.py" --macos-installer
else
  "$VENV_PY" "$ROOT/JumperlessAppPackagerOriginalAllPlatforms.py" --macos-installer
fi

if [[ "$CI" == "1" ]]; then
  step "CI staging — dist/macos + zip artifact"
  mkdir -p dist/macos builds
  rm -rf dist/macos/Jumperless.app
  cp -R dist/Jumperless.app dist/macos/
  DISABLE_MACOS_DMG=true "$VENV_PY" "$ROOT/Scripts/package_app.py" \
    --platform macos --arch arm64 --label "Jumperless-macOS-Apple-Silicon"
fi

echo ""
echo "================================"
echo "✅ Done"
echo "================================"
echo ""
echo "  DMG:  $DMG_OUT"
if [[ "$CI" == "1" ]]; then
  echo "  App:  $ROOT/dist/macos/Jumperless.app"
  echo "  Zip:  $ROOT/builds/Jumperless-macOS-Apple-Silicon.zip"
else
  echo "  App:  $ROOT/dist/Jumperless.app"
fi
echo ""
if [[ -f "$DMG_OUT" ]]; then
  ls -lh "$DMG_OUT"
fi
