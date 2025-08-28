#!/bin/bash
# Jumperless macOS Launcher
# Simple, stable launcher with terminal resizing

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "==============================================="
echo "       Jumperless macOS Launcher"
echo "==============================================="
echo ""

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Python 3 is not installed"
    echo ""
    echo "Please install Python 3:"
    echo "  • Download from python.org, or"
    echo "  • Install via Homebrew: brew install python3, or"
    echo "  • Use the system Python 3 (if available)"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "✅ Python found: $PYTHON_CMD"

# Check if pip is available
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    echo "❌ Error: pip is not available"
    echo "Please install pip or reinstall Python with pip included"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "✅ pip is available"

# Install requirements if requirements.txt exists
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    $PYTHON_CMD -m pip install -r "$SCRIPT_DIR/requirements.txt"
    if [ $? -ne 0 ]; then
        echo ""
        echo "⚠️  Warning: Failed to install some dependencies"
        echo "You may need to run: pip install -r requirements.txt"
        echo "Or use a virtual environment"
        echo ""
        read -p "Press Enter to continue anyway..."
    else
        echo "✅ Dependencies installed successfully"
    fi
fi

# Run the main application
echo ""
echo "==============================================="
echo "🚀 Starting Jumperless Bridge..."
echo "==============================================="
echo ""
cd "$SCRIPT_DIR"
exec $PYTHON_CMD JumperlessWokwiBridge.py "$@"
