#!/usr/bin/env bash
# Create a dedicated universal Python venv for macOS packaging (Intel + Apple Silicon).
#
# Uses an existing fat python.org interpreter when available (you may already have 3.12).
# Otherwise downloads and installs Python 3.11.9 (last 3.11 release with macOS installers).
#
# Usage:
#   ./Scripts/setup_universal_python.sh
#   source venv-packager/bin/activate
#   python JumperlessAppPackagerOriginalAllPlatforms.py

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON_INSTALL_VERSION="3.11.9"
PYTHON_INSTALL_MINOR="3.11"
VENV_DIR="$ROOT/venv-packager"
CACHE_DIR="$ROOT/.cache/python-installers"
PKG_NAME="python-${PYTHON_INSTALL_VERSION}-macos11.pkg"
PKG_URL="https://www.python.org/ftp/python/${PYTHON_INSTALL_VERSION}/${PKG_NAME}"

resolve_script="$ROOT/Scripts/resolve_universal_python.sh"
chmod +x "$resolve_script"

find_universal_python() {
  if "$resolve_script" 2>/dev/null; then
    return 0
  fi
  return 1
}

install_python_org() {
  mkdir -p "$CACHE_DIR"
  local pkg_path="$CACHE_DIR/$PKG_NAME"

  if [[ ! -f "$pkg_path" ]]; then
    echo "Downloading Python ${PYTHON_INSTALL_VERSION} universal installer..."
    curl -fL "$PKG_URL" -o "$pkg_path"
  fi

  echo ""
  echo "Installing Python ${PYTHON_INSTALL_VERSION} to /Library/Frameworks/Python.framework ..."
  echo "(macOS will ask for your admin password)"
  sudo installer -pkg "$pkg_path" -target /
}

echo "================================"
echo "Jumperless Universal Python Setup"
echo "================================"
echo ""

BASE_PY=""
if BASE_PY="$(find_universal_python)"; then
  echo "✅ Found universal interpreter: $BASE_PY"
  "$BASE_PY" --version
else
  echo "No universal python.org build detected."
  echo "Installing Python ${PYTHON_INSTALL_VERSION} (matches CI; last 3.11 with macOS pkg)..."
  install_python_org
  BASE_PY="$("/Library/Frameworks/Python.framework/Versions/${PYTHON_INSTALL_MINOR}/bin/python3")"
  if ! lipo -info "$BASE_PY" | grep -q x86_64 || ! lipo -info "$BASE_PY" | grep -q arm64; then
    echo "❌ Installed Python is not universal — something went wrong." >&2
    exit 1
  fi
  echo "✅ Installed: $BASE_PY"
  "$BASE_PY" --version
fi

echo ""
if [[ -d "$VENV_DIR" && "${JUMPERLESS_KEEP_VENV:-0}" == "1" ]]; then
  echo "Keeping existing venv: $VENV_DIR"
else
  if [[ -d "$VENV_DIR" ]]; then
    echo "Removing existing venv: $VENV_DIR"
    rm -rf "$VENV_DIR"
  fi
  echo "Creating venv at $VENV_DIR ..."
  "$BASE_PY" -m venv "$VENV_DIR"
fi

VENV_PY="$VENV_DIR/bin/python3"
echo ""
echo "Verifying venv interpreter..."
lipo -info "$VENV_PY"
"$VENV_PY" --version

echo ""
echo "Upgrading pip..."
"$VENV_PY" -m pip install --upgrade pip wheel setuptools

echo ""
echo "Installing packager requirements..."
"$VENV_PY" -m pip install --no-cache-dir -r "$ROOT/PackagingApps/packagerRequirements.txt"

echo ""
echo "Installing universal native dependencies (psutil, pyserial, ...)..."
export JUMPERLESS_PYTHON="$VENV_PY"
"$ROOT/Scripts/install_universal_deps.sh"

echo ""
echo "================================"
echo "✅ Ready for universal macOS builds"
echo "================================"
echo ""
echo "Activate the packager environment:"
echo "  source venv-packager/bin/activate"
echo ""
echo "Build:"
echo "  python JumperlessAppPackagerOriginalAllPlatforms.py"
echo ""
echo "Or without activating:"
echo "  venv-packager/bin/python JumperlessAppPackagerOriginalAllPlatforms.py"
echo ""
echo "This venv uses: $("$VENV_PY" --version) ($(lipo -info "$VENV_PY" | sed 's/.*: //'))"
