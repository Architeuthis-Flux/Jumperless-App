#!/usr/bin/env bash
# Build cross-platform PyPI/pipx launcher apps (thin wrapper, no bundled Python).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/tools/build_pipx_launcher.py" "$@"
