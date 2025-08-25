# Jumperless Python Fallback

This folder contains the Python source code version of Jumperless as a fallback option.

## Quick Start

### Option 1: Automatic Launcher (Recommended)

```bash
./run_jumperless.sh
```

Or double-click `run_jumperless.sh` in your file manager.

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

### macOS Security Warning
If you get a security warning about unidentified developer:
```bash
xattr -d com.apple.quarantine run_jumperless.sh
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

## Support

For support, visit: https://github.com/Architeuthis-Flux/JumperlessV5
