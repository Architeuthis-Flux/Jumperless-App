# Building Universal macOS Apps (Intel + Apple Silicon)

This document explains how to build universal (fat) binary macOS applications that run on both Intel (x86_64) and Apple Silicon (ARM64) Macs.

## Overview

As of this update, the Jumperless app packager now supports creating universal macOS applications that work on both Intel and Apple Silicon Macs. This is achieved through:

1. **Universal Python dependencies** - Installing Python packages with binaries that support both architectures
2. **PyInstaller universal2 target** - Using PyInstaller's `--target-arch universal2` flag
3. **Automated verification** - Checking that dependencies are universal before building

## Requirements

### Python Installation
Your Python installation must be universal (support both x86_64 and arm64). You can check this with:

```bash
lipo -info $(python3 -c "import sys; print(sys.executable)")
```

Expected output:
```
Architectures in the fat file: ... are: x86_64 arm64
```

The official Python.org installers for macOS 10.9+ are universal by default.

### Xcode Command Line Tools
You need Xcode Command Line Tools to compile universal binaries:

```bash
xcode-select --install
```

## Building Universal Apps Locally

### Step 1: Install Universal Dependencies

Before building, you must install Python dependencies with universal binary support:

```bash
./Scripts/install_universal_deps.sh
```

This script will:
- ✅ Verify Python is universal
- 🗑️ Uninstall architecture-specific packages
- 📦 Reinstall packages with universal binaries
- ✅ Verify the installation

**What it does internally:**
- Sets `ARCHFLAGS="-arch x86_64 -arch arm64"` environment variable
- Sets `_PYTHON_HOST_PLATFORM="macosx-10.9-universal2"` 
- Rebuilds packages with C extensions from source using `--no-binary :all:`
- Verifies key packages (psutil, pyserial) are universal using `lipo -info`

### Step 2: Run the Packager

Once dependencies are installed, run the packager as usual:

```bash
python3 JumperlessAppPackagerOriginalAllPlatforms.py
```

The packager will:
1. **Check dependencies** - Verify they are universal
2. **Prompt if not universal** - Ask if you want to continue anyway
3. **Build with PyInstaller** - Using `--target-arch universal2`
4. **Create DMG** - With the universal app

If dependencies are not universal, you'll see:
```
⚠️  WARNING: Some dependencies are not universal binaries!
   The resulting app will only work on the current architecture.
   To create a universal app, run:
   ./Scripts/install_universal_deps.sh

   Continue anyway? (y/n):
```

## CI/CD (GitHub Actions)

The GitHub Actions workflows have been updated to automatically build universal binaries:

### Main CLI Build Workflow
- File: `.github/workflows/build-and-package.yml`
- Automatically installs universal dependencies on macOS runners
- Uses PyInstaller with `--target-arch universal2`
- Verifies dependencies are universal before building

### GUI Build Workflow  
- File: `.github/workflows/build-gui-version.yml`
- Same universal dependency installation
- Uses `JumperlessGUI.spec` with `target_arch='universal2'`

**Note:** The GUI workflow currently builds separate Intel and Apple Silicon versions. You could simplify this to build a single universal binary by using only one macOS runner.

## Technical Details

### Why Some Dependencies Need Special Handling

Python packages with C extensions (native code) are compiled for specific architectures. Common packages that need universal binaries:

1. **psutil** - System and process utilities (has C extensions for macOS)
2. **pyserial** - Serial port access (has some native code)
3. **PySide6** - Qt bindings (extensive C++ code, usually comes as universal wheels)

Pure Python packages (like `requests`, `beautifulsoup4`, `packaging`) don't need special handling as they have no architecture-specific binaries.

### The Universal Build Process

1. **Compile-time:** When installing packages with `ARCHFLAGS="-arch x86_64 -arch arm64"`, the C compiler creates "fat" binaries containing code for both architectures:
   ```bash
   # Before (ARM64 only):
   Non-fat file: _psutil_osx.abi3.so is architecture: arm64
   
   # After (Universal):
   Architectures in the fat file: _psutil_osx.abi3.so are: x86_64 arm64
   ```

2. **PyInstaller packaging:** With `--target-arch universal2`, PyInstaller:
   - Includes Python interpreter for both architectures
   - Includes all dependencies with both architectures
   - Creates a universal executable that selects the right architecture at runtime

3. **Runtime:** When a user launches the app, macOS automatically runs the appropriate architecture:
   - On Intel Macs → runs x86_64 code
   - On Apple Silicon Macs → runs arm64 code natively (fast!)
   - Rosetta 2 is NOT needed because native code for both architectures is included

### Troubleshooting

#### Problem: Dependencies still ARM64-only after running script

**Solution 1:** Make sure you're using a universal Python:
```bash
lipo -info $(python3 -c "import sys; print(sys.executable)")
```

**Solution 2:** If using a virtual environment, recreate it with universal Python:
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
./Scripts/install_universal_deps.sh
```

#### Problem: PyInstaller build fails with "fat file errors"

This usually means some dependencies are not universal. Run the verification:
```bash
python3 -c "
import subprocess, glob, site
site_packages = site.getsitepackages()[0]
binaries = glob.glob(f'{site_packages}/psutil/_psutil_*.so')
for binary in binaries:
    result = subprocess.run(['lipo', '-info', binary], capture_output=True, text=True)
    print(f'{binary}:\n  {result.stdout}')
"
```

#### Problem: App works on my Mac but not on Intel/Apple Silicon

If you didn't use universal dependencies, the app will only work on the architecture you built it on. Rebuild with universal dependencies.

#### Problem: Build is much larger

Universal binaries are approximately 2x the size of single-architecture builds because they contain code for both architectures. This is expected and worth the compatibility.

## File Size Impact

A universal binary typically:
- **Executable:** ~2x the size of a single-architecture build
- **Total app bundle:** ~1.5-1.8x size (because many assets are architecture-independent)

Example:
- ARM64-only app: ~180 MB
- Universal app: ~270 MB

This is a reasonable trade-off for compatibility across all modern Macs.

## Future Improvements

1. **Automatic installation:** The packager could automatically run `install_universal_deps.sh` if dependencies are not universal
2. **Caching:** CI/CD could cache universal dependencies to speed up builds
3. **Single GUI build:** Simplify the GUI workflow to build one universal binary instead of separate Intel/ARM builds

## References

- [PyInstaller macOS Support](https://pyinstaller.org/en/stable/usage.html#macos-specific-options)
- [Apple Universal Binaries](https://developer.apple.com/documentation/apple-silicon/building-a-universal-macos-binary)
- [Python macOS Universal2](https://github.com/pypa/packaging-problems/issues/426)

## Summary

Creating universal macOS apps requires:
1. ✅ Universal Python installation
2. ✅ Universal Python dependencies (use `install_universal_deps.sh`)
3. ✅ PyInstaller with `--target-arch universal2`
4. ✅ Verification before building

The packager now handles this automatically and warns if dependencies are not universal.


