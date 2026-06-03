#!/bin/bash
# Install Python dependencies with universal (x86_64 + arm64) binaries for macOS
# This is required to create universal2 app bundles with PyInstaller
#
# Prefer the packager venv created by Scripts/setup_universal_python.sh.
# Override with JUMPERLESS_PYTHON=/path/to/python3

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ -n "${JUMPERLESS_PYTHON:-}" ]]; then
  PYTHON="$JUMPERLESS_PYTHON"
elif [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python3" ]]; then
  PYTHON="${VIRTUAL_ENV}/bin/python3"
elif [[ -x "$ROOT/venv-packager/bin/python3" ]]; then
  PYTHON="$ROOT/venv-packager/bin/python3"
elif PY="$("$ROOT/Scripts/resolve_universal_python.sh" 2>/dev/null)"; then
  PYTHON="$PY"
else
  PYTHON="python3"
fi

PIP() { "$PYTHON" -m pip "$@"; }

echo "================================"
echo "Installing Universal Dependencies"
echo "================================"
echo "Using Python: $PYTHON"
"$PYTHON" --version

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is only for macOS"
    exit 1
fi

# Check if Python is universal
PYTHON_ARCH=$(lipo -info "$PYTHON" 2>/dev/null || echo "")
if [[ $PYTHON_ARCH == *"x86_64"* && $PYTHON_ARCH == *"arm64"* ]]; then
    echo "✅ Python is universal (x86_64 + arm64)"
else
    echo "❌ Python is not universal — cannot install universal2 dependencies." >&2
    echo "   Architecture info: $PYTHON_ARCH" >&2
    echo "   Run: ./Scripts/setup_universal_python.sh" >&2
    exit 1
fi

# Set environment variables for universal builds
export ARCHFLAGS="-arch x86_64 -arch arm64"
export _PYTHON_HOST_PLATFORM="macosx-10.9-universal2"

echo ""
echo "📦 Uninstalling existing packages..."
# Uninstall packages that need to be rebuilt, plus optional arm64-only extras
# that break universal2 PyInstaller builds when present in a shared env.
PIP uninstall -y psutil pyserial PySide6 brotli brotlicffi 2>/dev/null || true

echo ""
echo "📦 Installing dependencies with universal binary support..."
echo "   ARCHFLAGS: $ARCHFLAGS"
echo "   _PYTHON_HOST_PLATFORM: $_PYTHON_HOST_PLATFORM"

# Install packages that are pure Python (no compilation needed)
echo ""
echo "Installing pure Python packages..."
PIP install --no-cache-dir beautifulsoup4 packaging requests pyduinocli

# Install packages with C extensions - force rebuild from source for universal binaries
echo ""
echo "Installing packages with C extensions (building from source for universal binaries)..."
PIP install --no-cache-dir --no-binary :all: psutil pyserial

echo ""
echo "================================"
echo "Verifying Installation"
echo "================================"

# Check if key dependencies are universal
echo ""
echo "Checking psutil architecture..."
PSUTIL_SO=$(find "$("$PYTHON" -c "import site; print(site.getsitepackages()[0])")" -name "_psutil_osx*.so" | head -1)
if [ -f "$PSUTIL_SO" ]; then
    PSUTIL_ARCH=$(lipo -info "$PSUTIL_SO" 2>/dev/null || echo "unknown")
    if [[ $PSUTIL_ARCH == *"x86_64"* && $PSUTIL_ARCH == *"arm64"* ]]; then
        echo "   ✅ psutil is universal (x86_64 + arm64)"
    else
        echo "   ⚠️  psutil architecture: $PSUTIL_ARCH"
        echo "   ⚠️  This may result in an ARM64-only app"
    fi
else
    echo "   ⚠️  Could not find psutil binary to verify"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "You can now run the packager with universal binary support."
echo "PyInstaller will use --target-arch universal2 to create a universal app."
