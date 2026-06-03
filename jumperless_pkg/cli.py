#!/usr/bin/env python3
"""
Jumperless CLI Entry Point

This module provides the main entry point for the jumperless command-line application.
When installed via pip or pipx, users can run 'jumperless' to start the application.
"""

import sys
import os


def main():
    """
    Main entry point for the jumperless CLI application.
    
    This function is called when users run 'jumperless' from the command line
    after installing the package with pip or pipx.
    
    pipx automatically creates an isolated virtual environment for the application,
    ensuring all dependencies are contained and don't conflict with other packages.
    """
    # Import the main function from the bridge module
    from jumperless_pkg.bridge import main as bridge_main
    
    # Run the application
    try:
        bridge_main()
    except KeyboardInterrupt:
        print("\n\nJumperless app terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

