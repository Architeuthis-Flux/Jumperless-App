# Universal macOS Build - Quick Start

Building a universal macOS app (Intel + Apple Silicon)? Here's what you need to know:

## TL;DR

```bash
# 1. Install universal dependencies
./Scripts/install_universal_deps.sh

# 2. Build as usual
python3 JumperlessAppPackagerOriginalAllPlatforms.py
```

That's it! The packager will verify dependencies and build a universal app.

## What Changed?

### Before (ARM64-only build)
```bash
# Dependencies were ARM64-only
lipo -info _psutil_osx.abi3.so
# Output: Non-fat file: ... is architecture: arm64

# PyInstaller created ARM64-only app
# ❌ Wouldn't run on Intel Macs
```

### After (Universal build)
```bash
# Dependencies are now universal (fat binaries)
lipo -info _psutil_osx.abi3.so
# Output: Architectures in the fat file: ... are: x86_64 arm64

# PyInstaller creates universal app
# ✅ Runs natively on both Intel and Apple Silicon!
```

## The Problem

When you install Python packages with pip on an ARM64 Mac, they get compiled for ARM64 only. PyInstaller then creates an ARM64-only app, which won't run on Intel Macs.

## The Solution

**Key changes:**

1. **New installation script:** `Scripts/install_universal_deps.sh`
   - Sets `ARCHFLAGS="-arch x86_64 -arch arm64"`
   - Rebuilds packages with C extensions for both architectures
   - Verifies binaries are universal

2. **Updated packager:** `JumperlessAppPackagerOriginalAllPlatforms.py`
   - Checks dependencies before building
   - Uses `--target-arch universal2` with PyInstaller
   - Warns if dependencies aren't universal

3. **Updated CI/CD:** GitHub Actions workflows
   - Automatically install universal dependencies
   - Build universal binaries in CI

## Which Dependencies Need This?

**Need universal binaries** (have C extensions):
- ✅ `psutil` - System utilities
- ✅ `pyserial` - Serial communication
- ✅ `PySide6` - Qt GUI framework

**Don't need special handling** (pure Python):
- `requests`
- `beautifulsoup4`
- `packaging`
- `pyduinocli`

## Verification

Check if dependencies are universal:

```bash
# Quick check
python3 -c "
import subprocess, glob, site
binaries = glob.glob(site.getsitepackages()[0] + '/psutil/_psutil_*.so')
for b in binaries[:1]:
    result = subprocess.run(['lipo', '-info', b], capture_output=True, text=True)
    print(result.stdout)
"
```

Expected output:
```
Architectures in the fat file: ... are: x86_64 arm64
```

## File Size Impact

Universal apps are larger because they contain code for both architectures:
- ARM64-only: ~180 MB
- Universal: ~270 MB (~1.5x larger)

This is a reasonable trade-off for compatibility!

## Troubleshooting

**"Some dependencies are not universal binaries!"**
→ Run `./Scripts/install_universal_deps.sh`

**Build fails with architecture errors**
→ Make sure Python itself is universal:
```bash
lipo -info $(python3 -c "import sys; print(sys.executable)")
```

**App works on my Mac but not on Intel/Apple Silicon**
→ Rebuild with universal dependencies

## More Details

See `BridgeDocs/UNIVERSAL_MACOS_BUILD.md` for:
- Technical details
- CI/CD integration
- Advanced troubleshooting
- Architecture explanations

---

**Bottom line:** Run the install script once, then build normally. The packager handles the rest! 🎉


