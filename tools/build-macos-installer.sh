#!/usr/bin/env bash
# End-to-end macOS build:
#   1. Universal python.org venv (venv-packager/) with universal deps
#   2. PyInstaller universal2 Jumperless.app (Scripts/build_macos_app.py)
#   3. Installer DMG (Scripts/createDMG.sh)
#
# Usage:
#   ./tools/build-macos-installer.sh                 # full local build (app + unsigned DMG)
#   ./tools/build-macos-installer.sh --ci            # CI: app + zip artifact, no DMG yet
#   ./tools/build-macos-installer.sh --ci --dmg-only # CI: stage signed app + build DMG
#   ./tools/build-macos-installer.sh --fresh         # recreate venv from scratch
#   ./tools/build-macos-installer.sh --skip-setup    # app + DMG only (venv must exist)
#   ./tools/build-macos-installer.sh --skip-dmg-codesign
#
# Output dir precedence: $JUMPERLESS_OUTPUT_DIR > (CI ? builds : repo root)

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VENV_DIR="$ROOT/venv-packager"
VENV_PY="$VENV_DIR/bin/python3"

FRESH=0
SKIP_SETUP=0
CI=0
DMG_ONLY=0

usage() { sed -n '2,18p' "$0"; exit "${1:-0}"; }

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
  echo "This script is macOS only." >&2
  exit 1
fi

step() { echo ""; echo "================================"; echo "$1"; echo "================================"; }

# Resolve output directory + DMG path.
if [[ -n "${JUMPERLESS_OUTPUT_DIR:-}" ]]; then
  OUTPUT_DIR="$JUMPERLESS_OUTPUT_DIR"
elif [[ "$CI" == "1" ]]; then
  OUTPUT_DIR="$ROOT/builds"
else
  OUTPUT_DIR="$ROOT/local-builds/macos"
fi
mkdir -p "$OUTPUT_DIR"
DMG_OUT="${JUMPERLESS_DMG_OUTPUT:-$OUTPUT_DIR/Jumperless-macOS.dmg}"

if [[ "$CI" == "1" ]]; then
  export JUMPERLESS_CI=1
  export JUMPERLESS_NONINTERACTIVE=1
fi

chmod +x "$ROOT"/Scripts/*.sh "$ROOT"/tools/*.sh 2>/dev/null || true

stage_and_build_dmg() {
  step "Stage Jumperless Python + create installer DMG"
  local app_src=""
  for c in "$ROOT/dist/macos/Jumperless.app" "$ROOT/dist/Jumperless.app"; do
    [[ -d "$c" ]] && { app_src="$c"; break; }
  done
  [[ -n "$app_src" ]] || { echo "No Jumperless.app found under dist/" >&2; exit 1; }

  local populate_py="$VENV_PY"
  [[ -x "$populate_py" ]] || populate_py="$(command -v python3)"
  "$populate_py" "$ROOT/Scripts/populate_jumperless_python.py" "$ROOT/Jumperless Python"

  rm -rf "$ROOT/JumperlessDMG"
  mkdir -p "$ROOT/JumperlessDMG"
  cp -R "$app_src" "$ROOT/JumperlessDMG/Jumperless.app"
  [[ -d "$ROOT/Jumperless Python" ]] && cp -R "$ROOT/Jumperless Python" "$ROOT/JumperlessDMG/Jumperless Python"

  JUMPERLESS_DMG_STAGING="$ROOT/JumperlessDMG" JUMPERLESS_DMG_OUTPUT="$DMG_OUT" \
    bash "$ROOT/Scripts/createDMG.sh"
  echo "DMG: $DMG_OUT"
}

# --dmg-only: skip the build, just (re)stage + create the DMG (used in CI after signing).
if [[ "$DMG_ONLY" == "1" ]]; then
  stage_and_build_dmg
  exit 0
fi

# --- Step 1: universal Python venv ---
step "Step 1/3 — Universal Python venv"
if [[ "$SKIP_SETUP" == "1" ]]; then
  [[ -x "$VENV_PY" ]] || { echo "--skip-setup but venv-packager missing." >&2; exit 1; }
  echo "Skipping venv setup (--skip-setup)"
elif [[ "$FRESH" == "1" || ! -x "$VENV_PY" ]]; then
  export JUMPERLESS_KEEP_VENV=0
  "$ROOT/Scripts/setup_universal_python.sh"
else
  echo "venv-packager exists — refreshing dependencies"
  export JUMPERLESS_PYTHON="$VENV_PY"
  export JUMPERLESS_KEEP_VENV=1
  "$ROOT/Scripts/setup_universal_python.sh"
fi
[[ -x "$VENV_PY" ]] || { echo "Packager venv missing after setup: $VENV_PY" >&2; exit 1; }
lipo -info "$VENV_PY" || true
"$VENV_PY" --version

# --- Step 2: build the .app ---
step "Step 2/3 — Build Jumperless.app"
"$VENV_PY" "$ROOT/Scripts/build_macos_app.py"

# Stage app under dist/macos/ (stable path for signing + packaging).
mkdir -p "$ROOT/dist/macos"
rm -rf "$ROOT/dist/macos/Jumperless.app"
cp -R "$ROOT/dist/Jumperless.app" "$ROOT/dist/macos/Jumperless.app"

# --- Step 3: package ---
step "Step 3/3 — Package"
if [[ "$CI" == "1" ]]; then
  # CI builds the zip artifact here; the DMG is built later via --dmg-only,
  # after the workflow has signed + notarized the .app.
  DISABLE_MACOS_DMG=true "$VENV_PY" "$ROOT/Scripts/package_app.py" \
    --platform macos --arch arm64 --label "Jumperless-macOS-Apple-Silicon" \
    --output-dir "$OUTPUT_DIR"
else
  # Local: produce the DMG now (unsigned unless a cert is configured).
  : "${SKIP_DMG_CODESIGN:=1}"; export SKIP_DMG_CODESIGN
  stage_and_build_dmg
fi

echo ""
echo "================================"
echo "Done"
echo "================================"
echo "  App:  $ROOT/dist/macos/Jumperless.app"
if [[ "$CI" == "1" ]]; then
  echo "  Zip:  $OUTPUT_DIR/Jumperless-macOS-Apple-Silicon.zip"
fi
if [[ -f "$DMG_OUT" ]]; then
  echo "  DMG:  $DMG_OUT"
  ls -lh "$DMG_OUT"
fi
exit 0
