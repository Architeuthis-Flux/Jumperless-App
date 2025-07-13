#!/usr/bin/env python3
"""
Modern Multi-Platform Packaging Script for Jumperless
Handles native executables, Python fallbacks, and platform-specific packaging
"""

import argparse
import os
import sys
import shutil
import pathlib
import subprocess
import zipfile
import tarfile
import json
from pathlib import Path

def create_python_fallback(platform, arch, output_dir):
    """Create Python fallback package with launcher script"""
    print(f"Creating Python fallback package for {platform}-{arch}")
    
    python_dir = output_dir / "Jumperless Python"
    python_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy main application
    if Path("JumperlessWokwiBridge.py").exists():
        shutil.copy2("JumperlessWokwiBridge.py", python_dir)
    
    # Copy requirements
    if Path("requirements.txt").exists():
        shutil.copy2("requirements.txt", python_dir)
    
    # Copy assets if they exist
    if Path("assets").exists():
        shutil.copytree("assets", python_dir / "assets", dirs_exist_ok=True)
    
    # Create launcher scripts
    create_launcher_scripts(python_dir, platform)
    
    # Create README for Python fallback
    create_python_readme(python_dir, platform)
    
    print(f"Python fallback package created in {python_dir}")

def create_launcher_scripts(python_dir, platform):
    """Create platform-specific launcher scripts"""
    
    # Universal Python launcher
    launcher_script = '''#!/usr/bin/env python3
"""
Jumperless Python Launcher
Automatically installs dependencies and runs the application
"""

import sys
import subprocess
import os
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        print("Please install dependencies manually:")
        print(f"  {sys.executable} -m pip install -r requirements.txt")
        return False

def main():
    """Main launcher function"""
    print("Jumperless Python Launcher")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("JumperlessWokwiBridge.py").exists():
        print("JumperlessWokwiBridge.py not found!")
        print("Please run this script from the 'Jumperless Python' directory")
        sys.exit(1)
    
    # Install dependencies if needed
    try:
        import serial
        import requests
        # Add other key imports here
    except ImportError:
        if not install_dependencies():
            sys.exit(1)
    
    # Run the main application
    print("Starting Jumperless...")
    try:
        # Import and run the main application
        spec = importlib.util.spec_from_file_location("Jumperless", "JumperlessWokwiBridge.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, 'main'):
            module.main()
        else:
            print("Warning: No main() function found in JumperlessWokwiBridge.py")
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import importlib.util
    main()
'''
    
    # Write universal launcher
    launcher_path = python_dir / "launcher.py"
    with open(launcher_path, 'w', encoding='utf-8') as f:
        f.write(launcher_script)
    
    if platform in ['linux', 'macos']:
        # Create shell script launcher
        shell_script = '''#!/bin/bash
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
'''
        
        script_path = python_dir / "run_jumperless.sh"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(shell_script)
        os.chmod(script_path, 0o755)
        
    if platform == 'windows':
        # Create batch file launcher
        batch_script = '''@echo off
REM Jumperless Windows Launcher
REM Finds Python and runs the application

echo Jumperless Windows Launcher
echo ==========================

REM Find Python
set PYTHON_CMD=
for %%i in (python.exe python3.exe py.exe) do (
    where /q %%i
    if not errorlevel 1 (
        set PYTHON_CMD=%%i
        goto found
    )
)

echo Python not found! Please install Python 3.9+ and try again.
pause
exit /b 1

:found
echo Using Python: %PYTHON_CMD%

REM Change to script directory
cd /d "%~dp0"

REM Run the launcher
%PYTHON_CMD% launcher.py %*
'''
        
        batch_path = python_dir / "run_jumperless.bat"
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_script)

def create_python_readme(python_dir, platform):
    """Create README for Python fallback"""
    
    readme_content = f'''# Jumperless Python Fallback

This folder contains the Python source code version of Jumperless as a fallback option.

## Quick Start

### Option 1: Automatic Launcher (Recommended)
'''
    
    if platform in ['linux', 'macos']:
        readme_content += '''
```bash
./run_jumperless.sh
```

Or double-click `run_jumperless.sh` in your file manager.
'''
    
    if platform == 'windows':
        readme_content += '''
```cmd
run_jumperless.bat
```

Or double-click `run_jumperless.bat` in Windows Explorer.
'''
    
    readme_content += '''
### Option 2: Manual Python Execution

1. Install Python 3.9+ from https://python.org
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python JumperlessWokwiBridge.py
   ```

## Requirements

- Python 3.9 or higher
- Dependencies listed in `requirements.txt`

## Troubleshooting

### Python Not Found
- Make sure Python is installed and in your PATH
- Try `python3` instead of `python` on Linux/macOS

### Permission Denied (Linux/macOS)
```bash
chmod +x run_jumperless.sh
./run_jumperless.sh
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

## Support

For support, visit: https://github.com/Architeuthis-Flux/JumperlessV5
'''
    
    readme_path = python_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

def package_platform(platform, arch, output_dir):
    """Package for specific platform"""
    print(f"Packaging for {platform} {arch}")
    
    platform_dir = output_dir / platform
    platform_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy executable if it exists
    executable_name = "Jumperless"
    if platform == "windows":
        executable_name += ".exe"
    
    executable_path = Path(f"dist/{platform}/{executable_name}")
    if executable_path.exists():
        shutil.copy2(executable_path, platform_dir)
        if platform != "windows":
            os.chmod(platform_dir / executable_name, 0o755)
        print(f"Copied executable: {executable_name}")
    else:
        print(f"Warning: Executable not found: {executable_path}")
    
    # Create Python fallback
    create_python_fallback(platform, arch, platform_dir)
    
    # Create main README
    create_platform_readme(platform_dir, platform)
    
    # Try platform-specific packaging
    if platform == "macos":
        try_create_macos_dmg(platform_dir, arch)
    
    print(f"{platform.title()} package created in {platform_dir}")

def try_create_macos_dmg(macos_dir, arch):
    """Try to create macOS DMG if create-dmg is available"""
    try:
        subprocess.run(["create-dmg", "--version"], check=True, capture_output=True)
        create_macos_dmg(macos_dir, arch)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("WARNING: create-dmg not available, skipping DMG creation")

def create_macos_dmg(macos_dir, arch):
    """Create macOS DMG"""
    print("Creating macOS DMG...")
    
    dmg_name = f"Jumperless-macOS-{arch}.dmg"
    
    # Create a temp directory without spaces for create-dmg
    temp_dir = Path(f"temp_dmg_{arch}")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    
    try:
        # Copy contents to temp directory with simpler names
        for item in macos_dir.iterdir():
            if item.is_dir():
                # Rename directories with spaces
                safe_name = item.name.replace(" ", "_")
                shutil.copytree(item, temp_dir / safe_name)
            else:
                shutil.copy2(item, temp_dir)
        
        # Basic DMG creation with simpler arguments
        cmd = [
        "create-dmg",
        "--volname", "Jumperless",
            "--window-size", "600", "400",
        "--icon-size", "100",
        dmg_name,
            str(temp_dir)
        ]
   
        subprocess.run(cmd, check=True)
        print(f"DMG created: {dmg_name}")

    except subprocess.CalledProcessError as e:
        print(f"Warning: DMG creation failed: {e}")
    finally:
        # Clean up temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def create_platform_readme(platform_dir, platform):
    """Create main README for platform"""
    
    platform_name = {
        "linux": "Linux",
        "macos": "macOS", 
        "windows": "Windows"
    }[platform]
    
    readme_content = f'''# Jumperless for {platform_name}

This package contains Jumperless built for {platform_name}.

## Quick Start

### Option 1: Native Executable (Recommended)
'''
    
    if platform == "linux":
        readme_content += '''
```bash
./Jumperless
```

Or double-click the executable in your file manager.
'''
    elif platform == "macos":
        readme_content += '''
```bash
./Jumperless
```

Or double-click the executable in Finder.
'''
    elif platform == "windows":
        readme_content += '''
Double-click `Jumperless.exe` or run from Command Prompt:
```cmd
Jumperless.exe
```
'''
    
    readme_content += '''
### Option 2: Python Fallback

If the native executable doesn't work, use the Python fallback:

1. Go to the `Jumperless Python` folder
2. Follow the instructions in that folder's README.md

## Package Contents

- `Jumperless''' + ('.exe' if platform == 'windows' else '') + '''` - Native executable
- `Jumperless Python/` - Python source code fallback
- `README.md` - This file

## System Requirements

- ''' + platform_name + ''' operating system
- No additional dependencies for native executable
- Python 3.9+ for Python fallback

## Troubleshooting

### Native Executable Issues
- Try running from terminal/command prompt to see error messages
- Use the Python fallback if native executable fails

### Need Help?
- Visit: https://github.com/Architeuthis-Flux/JumperlessV5
- Discord: https://discord.gg/TcjM5uEgb4

## License

See LICENSE file for details.
'''
    
    readme_path = platform_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

def create_archives(platform, output_dir):
    """Create compressed archives of the packages"""
    print(f"Creating archives for {platform}")
    
    platform_dir = output_dir / platform
    if not platform_dir.exists():
        print(f"WARNING: No {platform} directory found")
        return
    
    # Create ZIP archive (universal)
    zip_path = output_dir / f"Jumperless-{platform.title()}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(platform_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(platform_dir)
                zipf.write(file_path, arcname)
    
    # Create tar.gz for Linux/macOS
    if platform in ['linux', 'macos']:
        tar_path = output_dir / f"Jumperless-{platform.title()}.tar.gz"
        with tarfile.open(tar_path, 'w:gz') as tar:
            tar.add(platform_dir, arcname=f"Jumperless-{platform.title()}")
    
    print(f"Archives created for {platform}")

def main():
    """Main packaging function"""
    parser = argparse.ArgumentParser(description="Package Jumperless for specific platform")
    parser.add_argument("--platform", required=True, choices=["linux", "macos", "windows"])
    parser.add_argument("--arch", required=True, choices=["x64", "arm64"])
    
    args = parser.parse_args()
    
    print(f"Packaging Jumperless for {args.platform}-{args.arch}")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path("builds")
    output_dir.mkdir(exist_ok=True)
    
    # Platform-specific packaging
    package_platform(args.platform, args.arch, output_dir)
    
    # Create archives
    create_archives(args.platform, output_dir)
    
    print(f"\nPackaging complete for {args.platform}-{args.arch}!")
    print(f"Output directory: {output_dir}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 