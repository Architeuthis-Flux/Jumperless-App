#!/bin/bash
# Install Python dependencies with universal (x86_64 + arm64) binaries for macOS
# This is required to create universal2 app bundles with PyInstaller

set -e

echo "================================"
echo "Installing Universal Dependencies"
echo "================================"

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is only for macOS"
    exit 1
fi

# Check if Python is universal
PYTHON_ARCH=$(lipo -info $(python3 -c "import sys; print(sys.executable)") 2>/dev/null || echo "")
if [[ $PYTHON_ARCH == *"x86_64"* && $PYTHON_ARCH == *"arm64"* ]]; then
    echo "✅ Python is universal (x86_64 + arm64)"
else
    echo "⚠️  Warning: Python may not be universal. Build may fail."
    echo "   Architecture info: $PYTHON_ARCH"
fi

# Set environment variables for universal builds
export ARCHFLAGS="-arch x86_64 -arch arm64"
export _PYTHON_HOST_PLATFORM="macosx-10.9-universal2"

echo ""
echo "📦 Uninstalling existing packages..."
# Uninstall packages that need to be rebuilt
python3 -m pip uninstall -y psutil pyserial PySide6 2>/dev/null || true

echo ""
echo "📦 Installing dependencies with universal binary support..."
echo "   ARCHFLAGS: $ARCHFLAGS"
echo "   _PYTHON_HOST_PLATFORM: $_PYTHON_HOST_PLATFORM"

# Install packages that are pure Python (no compilation needed)
echo ""
echo "Installing pure Python packages..."
python3 -m pip install --no-cache-dir beautifulsoup4 packaging requests pyduinocli

# Install packages with C extensions - force rebuild from source for universal binaries
echo ""
echo "Installing packages with C extensions (building from source for universal binaries)..."
python3 -m pip install --no-cache-dir --no-binary :all: psutil pyserial

# PySide6 is tricky - try to install, but it may only have prebuilt wheels
echo ""
echo "Installing PySide6 (GUI support)..."
# First try with prebuilt wheels (they should be universal on modern versions)
python3 -m pip install --no-cache-dir PySide6>=6.6.0 websockets>=12.0 || {
    echo "⚠️  Warning: Could not install PySide6. GUI version may not work."
}

# Install platform-specific packages
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo ""
    echo "Installing macOS-specific packages..."
    # pyobjc packages should be universal on modern macOS
    python3 -m pip install --no-cache-dir pyobjc-framework-Cocoa 2>/dev/null || echo "⚠️  Could not install pyobjc (optional)"
fi

echo ""
echo "================================"
echo "Verifying Installation"
echo "================================"

# Check if key dependencies are universal
echo ""
echo "Checking psutil architecture..."
PSUTIL_SO=$(find $(python3 -c "import site; print(site.getsitepackages()[0])") -name "_psutil_osx*.so" | head -1)
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

