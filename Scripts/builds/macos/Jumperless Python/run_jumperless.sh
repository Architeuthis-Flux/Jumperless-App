#!/bin/bash
# Jumperless Shell Launcher
# Finds Python and runs the application

echo "Jumperless Shell Launcher"
echo "=========================="

# Find Python
PYTHON_CMD=""
for cmd in python3 python python3.11 python3.10 python3.9; do
    if command -v "$cmd" &> /dev/null; then
        PYTHON_CMD="$cmd"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "Python not found! Please install Python 3.9+ and try again."
    exit 1
fi

echo "Using Python: $PYTHON_CMD"

# Change to script directory
cd "$(dirname "$0")"

# Run the launcher
exec "$PYTHON_CMD" launcher.py "$@"
