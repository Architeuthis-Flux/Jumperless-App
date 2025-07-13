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
    shutil.copy2("JumperlessWokwiBridge.py", python_dir)
    
    # Copy requirements
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
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("Please install dependencies manually:")
        print(f"  {sys.executable} -m pip install -r requirements.txt")
        return False

def main():
    """Main launcher function"""
    print("Jumperless Python Launcher")
    #print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("JumperlessWokwiBridge.py").exists():
        print("❌ JumperlessWokwiBridge.py not found!")
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
        import JumperlessWokwiBridge
        JumperlessWokwiBridge.main()
    except Exception as e:
        print(f"❌ Error running application: {e}")
        sys.exit(1)

if __name__ == "__main__":
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
    echo "❌ Python not found! Please install Python 3.9+ and try again."
    exit 1
fi

echo "🐍 Using Python: $PYTHON_CMD"

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

echo ❌ Python not found! Please install Python 3.9+ and try again.
pause
exit /b 1

:found
echo 🐍 Using Python: %PYTHON_CMD%

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

### Virtual Environment (Advanced)
```bash
python -m venv jumperless_env
source jumperless_env/bin/activate  # Linux/macOS
# or
jumperless_env\\Scripts\\activate  # Windows
pip install -r requirements.txt
python JumperlessWokwiBridge.py
```

## Support

For support, visit: https://github.com/Architeuthis-Flux/JumperlessV5
'''
    
    readme_path = python_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

def package_linux(arch, output_dir):
    """Package for Linux using existing Linux packager"""
    print(f"Packaging for Linux {arch}")
    
    # Use existing packager
    if Path("Packager/JumperlessAppPackagerLinux.py").exists():
        subprocess.run([sys.executable, "Packager/JumperlessAppPackagerLinux.py"], check=True)
    else:
        print("WARNING: Linux packager not found, creating basic package")
        
    # Create basic Linux package structure
    linux_dir = output_dir / "linux"
    linux_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    if Path("dist/linux/JumperlessWokwiBridge").exists():
        shutil.copy2("dist/linux/JumperlessWokwiBridge", linux_dir)
        os.chmod(linux_dir / "JumperlessWokwiBridge", 0o755)
    
    # Create Python fallback
    create_python_fallback("linux", arch, linux_dir)
    
    # Create main README
    create_platform_readme(linux_dir, "linux")
    
    print(f"Linux package created in {linux_dir}")

def package_macos(arch, output_dir):
    """Package for macOS"""
    print(f"Packaging for macOS {arch}")
    
    macos_dir = output_dir / "macos"
    macos_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    if Path("dist/macos/JumperlessWokwiBridge").exists():
        shutil.copy2("dist/macos/JumperlessWokwiBridge", macos_dir)
        os.chmod(macos_dir / "JumperlessWokwiBridge", 0o755)
    
    # Create Python fallback
    create_python_fallback("macos", arch, macos_dir)
    
    # Create main README
    create_platform_readme(macos_dir, "macos")
    
    # Try to create DMG if create-dmg is available
    try:
        subprocess.run(["create-dmg", "--version"], check=True, capture_output=True)
        create_macos_dmg(macos_dir, arch)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("WARNING: create-dmg not available, skipping DMG creation")
    
    print(f"macOS package created in {macos_dir}")

def create_macos_dmg(macos_dir, arch):
    """Create macOS DMG"""
    print("Creating macOS DMG...")
    
    dmg_name = f"Jumperless-macOS-{arch}.dmg"
    
    # Basic DMG creation
    subprocess.run([
        "create-dmg",
        "--volname", "Jumperless",
        "--volicon", "icon.icns",
        "--background", "JumperlessWokwiDMGwindow4x.png",
        "--window-pos", "240", "240",
        "--window-size", "580", "590",
        "--icon-size", "100",
        "--icon", "Jumperless.app", "72", "245",
        "--app-drop-link", "395", "245",
        "--hide-extension", "Jumperless.app",
        "--codesign", "Kevin Cappuccio (LK2RWK9EUK)",
        "--add-folder", "Jumperless Python", "Jumperless Python", "69", "460",
        dmg_name,
        str(macos_dir)
    ], check=True)
   
    print(f"DMG created: {dmg_name}")

def package_windows(arch, output_dir):
    """Package for Windows"""
    print(f"Packaging for Windows {arch}")
    
    windows_dir = output_dir / "windows"
    windows_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    if Path("dist/windows/JumperlessWokwiBridge.exe").exists():
        shutil.copy2("dist/windows/JumperlessWokwiBridge.exe", windows_dir)
    
    # Create Python fallback
    create_python_fallback("windows", arch, windows_dir)
    
    # Create main README
    create_platform_readme(windows_dir, "windows")
    
    print(f"Windows package created in {windows_dir}")

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
./JumperlessWokwiBridge
```

Or double-click the executable in your file manager.
'''
    elif platform == "macos":
        readme_content += '''
```bash
./JumperlessWokwiBridge
```

Or double-click the executable in Finder.
'''
    elif platform == "windows":
        readme_content += '''
Double-click `JumperlessWokwiBridge.exe` or run from Command Prompt:
```cmd
JumperlessWokwiBridge.exe
```
'''
    
    readme_content += '''
### Option 2: Python Fallback

If the native executable doesn't work, use the Python fallback:

1. Go to the `Jumperless Python` folder
2. Follow the instructions in that folder's README.md

## Package Contents

- `JumperlessWokwiBridge''' + ('.exe' if platform == 'windows' else '') + '''` - Native executable
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
    if args.platform == "linux":
        package_linux(args.arch, output_dir)
    elif args.platform == "macos":
        package_macos(args.arch, output_dir)
    elif args.platform == "windows":
        package_windows(args.arch, output_dir)
    
    # Create archives
    create_archives(args.platform, output_dir)
    
    print(f"\nPackaging complete for {args.platform}-{args.arch}!")
    print(f"Output directory: {output_dir}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 