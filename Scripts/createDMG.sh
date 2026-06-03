#!/usr/bin/env bash
# Build the macOS installer DMG (drag-to-Applications layout with background art).
#
# Expects a staging folder (default: JumperlessDMG/) containing at least:
#   Jumperless.app
#   Jumperless Python/   (optional, shown as a folder on the DMG)
#
# Environment overrides:
#   JUMPERLESS_DMG_STAGING            staging directory (default: JumperlessDMG)
#   JUMPERLESS_DMG_OUTPUT             output .dmg path (default: builds/Jumperless-Installer.dmg)
#   JUMPERLESS_DMG_CODESIGN_IDENTITY  passed to create-dmg --codesign (default: Developer ID Application: …)
#   SKIP_DMG_CODESIGN=1               skip DMG codesign entirely

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STAGING="${JUMPERLESS_DMG_STAGING:-JumperlessDMG}"
OUTPUT="${JUMPERLESS_DMG_OUTPUT:-builds/Jumperless-Installer.dmg}"
IDENTITY="${JUMPERLESS_DMG_CODESIGN_IDENTITY:-Developer ID Application: Kevin Cappuccio (LK2RWK9EUK)}"

ICON="assets/icons/icon.icns"
BACKGROUND="assets/JumperlessWokwiDMGwindow4x.png"

if [ ! -d "$STAGING" ]; then
  echo "ERROR: DMG staging folder not found: $STAGING" >&2
  exit 1
fi
if [ ! -d "$STAGING/Jumperless.app" ]; then
  echo "ERROR: $STAGING/Jumperless.app not found" >&2
  exit 1
fi
if [ ! -f "$ICON" ]; then
  echo "ERROR: volume icon not found: $ICON" >&2
  exit 1
fi
if [ ! -f "$BACKGROUND" ]; then
  echo "ERROR: DMG background not found: $BACKGROUND" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT")"
rm -f "$OUTPUT"

cmd=(
  create-dmg
  --volname "Jumperless Installer"
  --volicon "$ICON"
  --background "$BACKGROUND"
  --window-pos 240 240
  --window-size 580 590
  --icon-size 100
  --icon "Jumperless.app" 72 245
  --app-drop-link 395 245
  --hide-extension "Jumperless.app"
)

if [ "${SKIP_DMG_CODESIGN:-0}" != "1" ]; then
  cmd+=(--codesign "$IDENTITY")
fi

if [ -d "$STAGING/Jumperless Python" ]; then
  cmd+=(--add-folder "Jumperless Python" "Jumperless Python" 69 460)
fi

cmd+=("$OUTPUT" "$STAGING/")

echo "Creating DMG: $OUTPUT"
echo "  staging: $STAGING"
"${cmd[@]}"
echo "DMG created: $OUTPUT"
