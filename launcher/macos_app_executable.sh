#!/bin/bash
# macOS .app bundle entry point — opens Terminal and runs uv_bootstrap.py.
APP_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RESOURCES="$APP_ROOT/Contents/Resources"
RUNNER="$RESOURCES/run_in_terminal.sh"
chmod +x "$RUNNER" "$RESOURCES/uv_bootstrap.py" 2>/dev/null || true
exec "$RUNNER" "$RESOURCES/uv_bootstrap.py"
