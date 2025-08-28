#!/usr/bin/env python3
"""
Create combined README for multi-platform releases
"""

import os
import sys
from pathlib import Path

def create_combined_readme():
    """Create a comprehensive README for the combined release"""
    
    readme_content = '''# Jumperless Multi-Platform Release

Welcome to Jumperless! This release contains pre-built executables for all major platforms.

## Quick Start Guide

### 1. Choose Your Platform

Download the appropriate package for your system:

- **Linux x64**: `Jumperless-Linux-x64.tar.gz` or `Jumperless-Linux-x64.zip`
- **macOS Intel**: `Jumperless-macOS-Intel.tar.gz` or `Jumperless-macOS-Intel.zip`
- **macOS Apple Silicon**: `Jumperless-macOS-Apple-Silicon.tar.gz` or `Jumperless-macOS-Apple-Silicon.zip`
- **Windows x64**: `Jumperless-Windows-x64.zip`

### 2. Extract and Run

1. Extract the downloaded package
2. Look for the main executable:
   - Linux: `JumperlessWokwiBridge`
   - macOS: `JumperlessWokwiBridge`
   - Windows: `JumperlessWokwiBridge.exe`
3. Double-click to run, or run from terminal/command prompt

### 3. Alternative: Python Fallback

If the native executable doesn't work:

1. Go to the `Jumperless Python` folder in your extracted package
2. Follow the instructions in that folder's README.md

## Installation Methods

### Native Executable (Recommended)
- **Pros**: No dependencies, fast startup, easy to run
- **Cons**: Larger file size, platform-specific

### Python Fallback
- **Pros**: Cross-platform, can be modified, smaller download
- **Cons**: Requires Python installation, dependencies

## System Requirements

### For Native Executables
- **Linux**: x86_64 architecture, glibc 2.17+ (most distributions 2014+)
- **macOS**: macOS 10.15+ (Catalina or later)
- **Windows**: Windows 10 or later, x64 architecture

### For Python Fallback
- **All platforms**: Python 3.9 or later
- Dependencies will be automatically installed by the launcher

## Getting Started

### First Time Setup

1. **Hardware**: Connect your Jumperless device to your computer
2. **Software**: Run the Jumperless application
3. **Wokwi**: Open your Wokwi project in a web browser
4. **Connect**: Follow the on-screen instructions to link Wokwi to your hardware

### Basic Usage

1. Start the Jumperless application
2. Open your Wokwi project in a web browser
3. The application will automatically detect and connect to your project
4. Your virtual circuit will now control the physical hardware!

## Troubleshooting

### Native Executable Issues

#### Linux
```bash
# If permission denied
chmod +x JumperlessWokwiBridge
./JumperlessWokwiBridge

# If missing libraries
sudo apt-get install libfuse2  # For AppImage support
```

#### macOS
```bash
# If "unidentified developer" error
sudo xattr -r -d com.apple.quarantine JumperlessWokwiBridge

# If permission denied
chmod +x JumperlessWokwiBridge
./JumperlessWokwiBridge
```

#### Windows
- If Windows Defender blocks the executable, add an exception
- If missing DLLs, try installing Visual C++ Redistributable 2019+

### Python Fallback Issues

#### Python Not Found
```bash
# Install Python from python.org
# Or use package manager:
sudo apt-get install python3      # Ubuntu/Debian
brew install python3              # macOS
winget install Python.Python.3   # Windows
```

#### Dependencies Issues
```bash
# Update pip first
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Common Issues

#### Device Not Detected
- Check USB connection
- Try a different USB port
- Restart the application
- Check device drivers (Windows)

#### Wokwi Connection Issues
- Ensure Wokwi project is running
- Check browser console for errors
- Try refreshing the Wokwi page

## Advanced Usage

### Command Line Options

```bash
# Show help
./JumperlessWokwiBridge --help

# Specify port (if multiple devices)
./JumperlessWokwiBridge --port /dev/ttyUSB0    # Linux
./JumperlessWokwiBridge --port COM3           # Windows

# Debug mode
./JumperlessWokwiBridge --debug
```

### Configuration

The application creates a config file in:
- Linux: `~/.config/jumperless/config.json`
- macOS: `~/Library/Application Support/Jumperless/config.json`
- Windows: `%APPDATA%\\Jumperless\\config.json`

### Building from Source

If you want to build from source or contribute to development:

1. Clone the repository: `git clone https://github.com/Architeuthis-Flux/JumperlessV5`
2. Install dependencies: `pip install -r requirements.txt`
3. Run from source: `python JumperlessWokwiBridge.py`

## Support and Community

### Getting Help
- **GitHub Issues**: https://github.com/Architeuthis-Flux/JumperlessV5/issues
- **Discord Community**: https://discord.gg/TcjM5uEgb4
- **Documentation**: https://github.com/Architeuthis-Flux/JumperlessV5/wiki

### Contributing
We welcome contributions! Please see the GitHub repository for:
- Bug reports and feature requests
- Code contributions
- Documentation improvements
- Testing and feedback

## License

This project is open source. See the LICENSE file for details.

## Changelog

### Latest Release
- Multi-platform CI/CD pipeline
- Improved packaging with Python fallback
- Better error handling and logging
- Enhanced platform-specific optimizations
- Modern build system with GitHub Actions

### Previous Releases
See the GitHub releases page for complete changelog.

---

**Thank you for using Jumperless!** 🚀

For the latest updates and information, visit our GitHub repository at:
https://github.com/Architeuthis-Flux/JumperlessV5
'''
    
    # Write the combined README
    readme_path = Path("combined-release") / "README.md"
    readme_path.parent.mkdir(exist_ok=True)
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"Created combined README: {readme_path}")

if __name__ == "__main__":
    create_combined_readme() 