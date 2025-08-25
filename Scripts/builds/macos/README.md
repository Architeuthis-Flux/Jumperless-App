# Jumperless for macOS

This package contains Jumperless built for macOS.

## Quick Start

### Option 1: Native Executable (Recommended)

Double-click `Jumperless.app` in Finder to run. This will open a new Terminal window and run the Jumperless CLI application.

Or open from Terminal:
```bash
open Jumperless.app
```

The app will automatically launch in a new Terminal window for the best CLI experience.

**Important for macOS users:** If you get a security warning about the app being from an unidentified developer, you may need to:
1. Right-click the app and select "Open" to bypass Gatekeeper, OR
2. Remove the quarantine attribute:
   ```bash
   xattr -d com.apple.quarantine Jumperless.app
   ```

### Option 2: Python Fallback

If the native executable doesn't work, use the Python fallback:

1. Go to the `Jumperless Python` folder
2. Follow the instructions in that folder's README.md

## Package Contents

- `Jumperless.app` - Native executable
- `Jumperless Python/` - Python source code fallback
- `README.md` - This file

## System Requirements

- macOS operating system
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
