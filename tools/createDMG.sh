#!/usr/bin/env bash
# Local convenience wrapper — same DMG as CI, default output in repo root.
set -euo pipefail
export JUMPERLESS_DMG_OUTPUT="${JUMPERLESS_DMG_OUTPUT:-Jumperless_Installer.dmg}"
exec "$(dirname "$0")/../Scripts/createDMG.sh"
