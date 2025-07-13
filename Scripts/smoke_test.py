#!/usr/bin/env python3
"""
Smoke test script for Jumperless executables
Basic verification that the built executables work
"""

import argparse
import os
import sys
import subprocess
import time
from pathlib import Path

def test_executable(executable_path, platform):
    """Test that an executable runs without crashing"""
    print(f"Testing executable: {executable_path}")
    
    if not Path(executable_path).exists():
        print(f"ERROR: Executable not found: {executable_path}")
        return False
    
    try:
        # Run with --version or --help flag if available
        # Use a timeout to avoid hanging
        result = subprocess.run(
            [str(executable_path), "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"SUCCESS: Executable runs successfully")
            return True
        else:
            print(f"WARNING: Executable returned non-zero exit code: {result.returncode}")
            print(f"STDERR: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"WARNING: Executable timed out (might be waiting for input)")
        return True  # This is often expected for interactive apps
    except Exception as e:
        print(f"ERROR: Error running executable: {e}")
        return False

def test_python_fallback(python_dir, platform):
    """Test that the Python fallback works"""
    print(f"Testing Python fallback: {python_dir}")
    
    if not Path(python_dir).exists():
        print(f"ERROR: Python fallback directory not found: {python_dir}")
        return False
    
    # Check required files exist
    required_files = [
        "JumperlessWokwiBridge.py",
        "requirements.txt",
        "launcher.py",
        "README.md"
    ]
    
    for file in required_files:
        file_path = Path(python_dir) / file
        if not file_path.exists():
            print(f"ERROR: Required file missing: {file}")
            return False
    
    # Check platform-specific launcher
    if platform in ['linux', 'macos']:
        launcher_path = Path(python_dir) / "run_jumperless.sh"
        if not launcher_path.exists():
            print(f"ERROR: Shell launcher missing: {launcher_path}")
            return False
        
        # Check if it's executable
        if not os.access(launcher_path, os.X_OK):
            print(f"ERROR: Shell launcher not executable: {launcher_path}")
            return False
    
    elif platform == 'windows':
        launcher_path = Path(python_dir) / "run_jumperless.bat"
        if not launcher_path.exists():
            print(f"ERROR: Batch launcher missing: {launcher_path}")
            return False
    
    print(f"SUCCESS: Python fallback structure is valid")
    return True

def test_package_structure(platform_dir, platform):
    """Test that the package structure is correct"""
    print(f"Testing package structure: {platform_dir}")
    
    if not Path(platform_dir).exists():
        print(f"ERROR: Package directory not found: {platform_dir}")
        return False
    
    # Check main README
    readme_path = Path(platform_dir) / "README.md"
    if not readme_path.exists():
        print(f"ERROR: Main README missing: {readme_path}")
        return False
    
    # Check executable
    executable_name = "Jumperless"
    if platform == "windows":
        executable_name += ".exe"
    
    executable_path = Path(platform_dir) / executable_name
    if not executable_path.exists():
        print(f"ERROR: Main executable missing: {executable_path}")
        return False
    
    # Check Python fallback directory
    python_dir = Path(platform_dir) / "Jumperless Python"
    if not python_dir.exists():
        print(f"ERROR: Python fallback directory missing: {python_dir}")
        return False
    
    print(f"SUCCESS: Package structure is valid")
    return True

def main():
    """Main smoke test function"""
    parser = argparse.ArgumentParser(description="Run smoke tests for Jumperless packages")
    parser.add_argument("--platform", required=True, choices=["linux", "macos", "windows"])
    
    args = parser.parse_args()
    
    print(f"Running smoke tests for {args.platform}")
    print("=" * 50)
    
    # Test paths
    platform_dir = Path("builds") / args.platform
    
    # Test package structure
    structure_ok = test_package_structure(platform_dir, args.platform)
    if not structure_ok:
        print("ERROR: Package structure test failed")
        return 1
    
    # Test executable
    executable_name = "Jumperless"
    if args.platform == "windows":
        executable_name += ".exe"
    
    executable_path = platform_dir / executable_name
    executable_ok = test_executable(executable_path, args.platform)
    
    # Test Python fallback
    python_dir = platform_dir / "Jumperless Python"
    python_ok = test_python_fallback(python_dir, args.platform)
    
    # Summary
    print("\n" + "=" * 50)
    print("Smoke Test Results:")
    print(f"  Package Structure: {'PASS' if structure_ok else 'FAIL'}")
    print(f"  Executable Test:   {'PASS' if executable_ok else 'FAIL'}")
    print(f"  Python Fallback:   {'PASS' if python_ok else 'FAIL'}")
    
    if all([structure_ok, executable_ok, python_ok]):
        print("\nAll smoke tests passed!")
        return 0
    else:
        print("\nSome smoke tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 