#!/usr/bin/env python3
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
