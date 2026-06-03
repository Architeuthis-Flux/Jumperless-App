#!/usr/bin/env bash
# Build and (optionally) publish the `jumperless` package to PyPI.
#
# Usage:
#   ./tools/publish_pypi.sh             # sync bridge.py, build sdist+wheel, twine check
#   ./tools/publish_pypi.sh --test      # ... then upload to TestPyPI
#   ./tools/publish_pypi.sh --prod      # ... then upload to PyPI
#
# Auth: twine reads ~/.pypirc or TWINE_USERNAME/TWINE_PASSWORD
#       (username __token__, password = your pypi-… API token).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TARGET="check"
case "${1:-}" in
  ""|--check) TARGET="check" ;;
  --test) TARGET="test" ;;
  --prod) TARGET="prod" ;;
  -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
  *) echo "Unknown option: $1" >&2; exit 1 ;;
esac

PY="$(command -v python3 || command -v python)"
VERSION="$(tr -d '[:space:]' < VERSION)"
echo "==> jumperless $VERSION"

echo "==> Syncing jumperless_pkg/bridge.py from JumperlessWokwiBridge.py"
"$PY" Scripts/prepare_jumperless_pkg.py

echo "==> Building sdist + wheel"
rm -rf dist build ./*.egg-info
"$PY" -m build

echo "==> Validating with twine"
"$PY" -m twine check dist/*

case "$TARGET" in
  check)
    echo "==> Build OK. Artifacts in dist/ (no upload). Re-run with --test or --prod to publish."
    ;;
  test)
    echo "==> Uploading to TestPyPI"
    "$PY" -m twine upload --repository testpypi dist/*
    ;;
  prod)
    echo "==> Uploading to PyPI (production)"
    read -r -p "Publish jumperless $VERSION to production PyPI? (yes/no): " confirm
    [ "$confirm" = "yes" ] || { echo "Aborted."; exit 1; }
    "$PY" -m twine upload dist/*
    echo "==> Done: https://pypi.org/project/jumperless/$VERSION/"
    ;;
esac
