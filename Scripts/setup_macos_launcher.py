#!/usr/bin/env python3
"""
Setup macOS Launcher Script Hack
Applies the launcher script hack BEFORE code signing and notarization
"""

import os
import shutil
from pathlib import Path

def setup_macos_launcher_hack():
    """
    Implement the launcher script hack for macOS to get persistent terminal
    This happens BEFORE code signing so the signature applies to the final version
    """
    print("Setting up macOS launcher script hack...")
    
    app_path = Path("dist/macos/Jumperless.app")
    if not app_path.exists():
        print(f"Warning: App bundle not found at {app_path}")
        return False
    
    macos_dir = app_path / "Contents" / "MacOS"
    original_executable = macos_dir / "Jumperless"
    cli_executable = macos_dir / "Jumperless_cli"
    
    if not original_executable.exists():
        print(f"Warning: Original executable not found at {original_executable}")
        return False
    
    # Rename the original executable to Jumperless_cli
    if cli_executable.exists():
        cli_executable.unlink()
    shutil.move(str(original_executable), str(cli_executable))
    print(f"Renamed {original_executable} to {cli_executable}")
    
    # Create launcher script content
    launcher_script_content = '''#!/bin/bash
# Jumperless macOS Launcher
# Opens Terminal and runs the CLI application

# Get the directory of this script (inside the app bundle)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLI_EXECUTABLE="$SCRIPT_DIR/Jumperless_cli"

# Check if CLI executable exists
if [ ! -f "$CLI_EXECUTABLE" ]; then
    echo "Error: CLI executable not found at $CLI_EXECUTABLE"
    exit 1
fi

# Use AppleScript to open Terminal and run the CLI app
osascript -e "
tell application \\"Terminal\\"
    activate
    set newWindow to do script \\"\\"
    delay 0.5
    do script \\"cd '$SCRIPT_DIR' && ./Jumperless_cli\\" in newWindow
    set bounds of front window to {100, 100, 1000, 700}
end tell
"
'''
    
    # Write launcher script
    with open(original_executable, 'w') as f:
        f.write(launcher_script_content)
    
    # Make launcher script executable
    os.chmod(original_executable, 0o755)
    print(f"Created launcher script at {original_executable}")
    
    return True

if __name__ == "__main__":
    success = setup_macos_launcher_hack()
    if success:
        print("macOS launcher script hack applied successfully")
    else:
        print("Failed to apply macOS launcher script hack")
        exit(1) 