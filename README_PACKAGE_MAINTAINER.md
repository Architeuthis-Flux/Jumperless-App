# Jumperless PyPI Package - Maintainer Guide

## 📦 Package Overview

**Package Name**: `jumperless`  
**Current Version**: 1.1.1.14  
**PyPI URL**: https://pypi.org/project/jumperless/ (after publishing)  
**Installation**: `pipx install jumperless` or `pip install jumperless`

## 🗂️ File Structure

### Core Package Files
```
jumperless_pkg/              # Python package (installed to user's system)
├── __init__.py              # Package metadata and version
├── cli.py                   # Entry point - creates 'jumperless' command
├── bridge.py                # Main application (copy of JumperlessWokwiBridge.py)
└── assets/                  # Bundled assets (icons, config files)
    ├── avrdudeCustom.conf
    ├── example_sketch.ino
    └── icons/               # Application icons
```

### Configuration Files
```
pyproject.toml               # Package configuration (modern standard)
MANIFEST.in                  # File inclusion rules for distribution
requirements.txt             # Development reference (auto-included in pyproject.toml)
.gitignore                   # Excludes build artifacts
```

### Documentation
```
README_PYPI.md               # User-facing README (shown on PyPI)
PYPI_QUICKSTART.md          # Quick start for publishing
PYPI_PUBLISHING_GUIDE.md    # Detailed publishing instructions
PYPI_SETUP_COMPLETE.md      # Setup summary
```

### Helper Scripts
```
build_package.sh            # Automated build script
test_package_locally.sh     # Test installation in local venv
```

## 🔄 Development Workflow

### 1. Making Changes to the App

Edit the source file:
```bash
nano JumperlessWokwiBridge.py
# or use your preferred editor
```

### 2. Update Version Numbers

**CRITICAL**: Update in BOTH locations:

**File 1**: `pyproject.toml`
```toml
version = "1.1.1.15"  # Line 7
```

**File 2**: `JumperlessWokwiBridge.py`
```python
App_Version = "1.1.1.15"  # Line 7
```

### 3. Copy to Package

```bash
cp JumperlessWokwiBridge.py jumperless_pkg/bridge.py
```

### 4. Build & Publish

```bash
# Build
./build_package.sh

# Publish to PyPI
python3 -m twine upload dist/*
```

## 🎯 Installation Methods for End Users

### Method 1: pipx (Recommended - Automatic Isolation)

```bash
# One-time setup
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install Jumperless
pipx install jumperless

# Run anywhere
jumperless

# Update
pipx upgrade jumperless

# Uninstall
pipx uninstall jumperless
```

**What pipx does:**
- Creates isolated venv at `~/.local/pipx/venvs/jumperless/`
- Installs all dependencies there
- Links `jumperless` command to `~/.local/bin/`
- Zero dependency conflicts with other Python packages
- Command available globally

### Method 2: pip (Manual Isolation)

```bash
# Create venv
python3 -m venv ~/jumperless-env

# Activate
source ~/jumperless-env/bin/activate

# Install
pip install jumperless

# Run
jumperless

# Later: deactivate
deactivate
```

### Method 3: uv (Modern Fast Alternative)

```bash
# Install with uv (faster pip alternative)
uv pip install jumperless
```

## 📊 Package Information

### Dependencies (Auto-installed)
All dependencies from `requirements.txt` are automatically installed:

**Core Dependencies:**
- beautifulsoup4 ≥4.13.4 - HTML parsing for Wokwi
- packaging ≥24.1 - Version comparison
- psutil ≥5.9.8 - Process and system utilities
- pyduinocli ≥0.35.0 - Arduino CLI integration
- pyserial ≥3.5 - Serial communication
- requests ≥2.32.3 - HTTP requests
- colorama ≥0.4.6 - Cross-platform colors

**Platform-Specific (Auto-detected):**
- pywin32 ≥306 - Windows only
- pynput - Windows only (enhanced keyboard input)

**Optional (not auto-installed):**
- PySide6 ≥6.6.0 - GUI version
- websockets ≥12.0 - GUI version

### Package Sizes
- **Wheel** (.whl): ~12MB
- **Source** (.tar.gz): ~24MB

### Python Version Support
- Python 3.8+
- Tested on Python 3.8, 3.9, 3.10, 3.11, 3.12

### Platform Support
- ✅ Windows
- ✅ macOS (Intel and Apple Silicon)
- ✅ Linux (x86_64, ARM)

## 🔧 Maintenance Tasks

### Updating Dependencies

Edit `pyproject.toml`:
```toml
dependencies = [
    "beautifulsoup4>=4.13.4",
    # ... other deps
]
```

### Adding New Features

1. Edit `JumperlessWokwiBridge.py`
2. Update version (both files)
3. Copy to package: `cp JumperlessWokwiBridge.py jumperless_pkg/bridge.py`
4. Build and publish

### Testing Before Publishing

```bash
# Test locally
./test_package_locally.sh

# Or test on TestPyPI
python3 -m twine upload --repository testpypi dist/*
pipx install --index-url https://test.pypi.org/simple/ \
             --pip-args='--extra-index-url=https://pypi.org/simple/' \
             jumperless
```

## 📈 Version Number Strategy

Format: `MAJOR.MINOR.PATCH.BUILD`

**Current**: 1.1.1.14

**When to increment:**
- `MAJOR` (1.x.x.x): Breaking changes, incompatible API
- `MINOR` (x.1.x.x): New features, backwards compatible
- `PATCH` (x.x.1.x): Bug fixes, backwards compatible  
- `BUILD` (x.x.x.14): Build number, small tweaks

**Example progression:**
- Bug fix: 1.1.1.14 → 1.1.1.15
- New feature: 1.1.1.15 → 1.1.2.0
- Breaking change: 1.1.2.0 → 2.0.0.0

## 🔐 Security: API Tokens

### Creating PyPI API Token

1. Log in to https://pypi.org/
2. Account Settings → API tokens
3. "Add API token"
4. Name: "jumperless-upload"
5. Scope: "Entire account" (or specific project after first upload)
6. **COPY THE TOKEN** - you can't see it again!

### Storing Token Securely

Create `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcm...  # Your actual token
```

Set permissions:
```bash
chmod 600 ~/.pypirc
```

## 📝 Pre-Publishing Checklist

- [ ] Version updated in `pyproject.toml`
- [ ] Version updated in `JumperlessWokwiBridge.py`
- [ ] Latest code copied: `cp JumperlessWokwiBridge.py jumperless_pkg/bridge.py`
- [ ] Build succeeds: `./build_package.sh`
- [ ] Package checks pass: `python3 -m twine check dist/*`
- [ ] Tested locally: `./test_package_locally.sh`
- [ ] (Optional) Tested on TestPyPI
- [ ] Ready to publish: `python3 -m twine upload dist/*`

## 🐛 Troubleshooting

### "Package 'jumperless' already exists"
The package name might be taken on PyPI. Check: https://pypi.org/project/jumperless/

If taken, you'll need to choose a different name:
- Edit `pyproject.toml`: `name = "jumperless-bridge"`
- Rebuild and upload

### "HTTPError: 400 Bad Request - File already exists"
You can't re-upload the same version. Increment the version number.

### Version Mismatch
The build script checks if versions match:
```bash
./build_package.sh
# Look for "Version mismatch!" warning
```

### Import Errors After Installation
Make sure you copied the latest code:
```bash
cp JumperlessWokwiBridge.py jumperless_pkg/bridge.py
```

## 📚 Resources

- **Python Packaging Guide**: https://packaging.python.org/
- **PyPI Help**: https://pypi.org/help/
- **pipx Documentation**: https://pipx.pypa.io/
- **Semantic Versioning**: https://semver.org/

## 🎓 Understanding the Setup

### Why jumperless_pkg?

The package directory is called `jumperless_pkg` (not `jumperless`) because:
- The package NAME on PyPI is `jumperless` (in pyproject.toml)
- The Python module is `jumperless_pkg` (the directory)
- There was already a shell script called `jumperless` in the repo
- This avoids naming conflicts

### How Entry Points Work

In `pyproject.toml`:
```toml
[project.scripts]
jumperless = "jumperless_pkg.cli:main"
```

This means:
- Command name: `jumperless`
- Python module: `jumperless_pkg.cli`
- Function to call: `main()`

When installed, pip/pipx creates a script that calls `jumperless_pkg.cli.main()`.

### How pipx Provides Isolation

When a user runs `pipx install jumperless`:
1. pipx creates `~/.local/pipx/venvs/jumperless/`
2. Creates fresh virtual environment there
3. Runs `pip install jumperless` inside that venv
4. Creates symlink: `~/.local/bin/jumperless` → venv's script
5. User can run `jumperless` from anywhere
6. All dependencies stay in that isolated venv

**Result**: No conflicts, clean installation, easy updates!

## ✨ What's Different from Current Distribution

### Before (Current Method)
- Users download Python script directly
- Users manually install dependencies: `pip install -r requirements.txt`
- Users run: `python JumperlessWokwiBridge.py`
- Risk of dependency conflicts
- Harder to update

### After (PyPI Distribution)
- Users install from PyPI: `pipx install jumperless`
- Dependencies installed automatically
- Users run: `jumperless` (global command)
- Automatic virtual environment (with pipx)
- Easy updates: `pipx upgrade jumperless`

## 🎉 Summary

You now have:
- ✅ Professional PyPI package structure
- ✅ Modern pyproject.toml configuration
- ✅ Automatic virtual environment support (pipx)
- ✅ Cross-platform compatibility
- ✅ Automated build scripts
- ✅ Comprehensive documentation
- ✅ Package tested and verified

**Next step**: Create PyPI account and publish!

**After publishing, users can install with a single command:**
```bash
pipx install jumperless
```

**No manual venv creation, no dependency conflicts, just works! 🚀**

