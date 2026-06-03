# Jumperless PyPI Quick Start Guide

## 🎯 What We've Set Up

Your Jumperless app is now ready to be published to PyPI! Users will be able to install it with:

```bash
# Recommended (automatic virtual environment isolation)
pipx install jumperless

# Or with pip
pip install jumperless
```

## 📦 Package Structure Created

```
Jumperless-App/
├── jumperless_pkg/           # Python package directory
│   ├── __init__.py           # Package metadata
│   ├── cli.py                # CLI entry point
│   ├── bridge.py             # Main application (copy of JumperlessWokwiBridge.py)
│   └── assets/               # Asset files included in package
├── pyproject.toml            # Modern Python package configuration
├── MANIFEST.in               # Controls which files are included
├── README_PYPI.md            # PyPI-specific README
├── build_package.sh          # Build automation script
└── PYPI_PUBLISHING_GUIDE.md  # Detailed publishing instructions
```

## 🚀 Publishing to PyPI (First Time)

### Step 1: Create PyPI Account

1. Go to https://pypi.org/account/register/
2. Verify your email
3. Go to Account Settings → API tokens
4. Create a new token (name it "jumperless-upload")
5. **Save the token** - you can't see it again!

### Step 2: Build the Package

```bash
cd /Users/kevinsanto/Documents/GitHub/Jumperless-App
./build_package.sh
```

Or manually:
```bash
rm -rf dist/ build/ *.egg-info
python3 -m build
python3 -m twine check dist/*
```

### Step 3: Upload to TestPyPI (Test First!)

```bash
# Upload to test server
python3 -m twine upload --repository testpypi dist/*
```

When prompted:
- Username: `__token__`
- Password: `pypi-...` (your TestPyPI token)

### Step 4: Test Installation

```bash
# Test with pipx (recommended)
pipx install --index-url https://test.pypi.org/simple/ --pip-args='--extra-index-url=https://pypi.org/simple/' jumperless

# Run it
jumperless

# Cleanup after testing
pipx uninstall jumperless
```

### Step 5: Upload to Production PyPI

```bash
# Upload to real PyPI
python3 -m twine upload dist/*
```

When prompted:
- Username: `__token__`
- Password: `pypi-...` (your PyPI token)

## ✅ Done! Users Can Now Install

After publishing, users can install with:

```bash
# Recommended: pipx (automatic virtual environment)
pipx install jumperless
jumperless

# Or with pip
pip install jumperless
jumperless
```

## 🔄 Publishing Updates

When you make changes:

1. **Update version numbers** in BOTH files:
   - `pyproject.toml` → `version = "X.X.X.X"`
   - `jumperless_pkg/bridge.py` → `App_Version = "X.X.X.X"`

2. **Update the main script**:
   ```bash
   cp JumperlessWokwiBridge.py jumperless_pkg/bridge.py
   ```

3. **Build and publish**:
   ```bash
   ./build_package.sh
   python3 -m twine upload dist/*
   ```

## 🎨 What Makes This Special

### Automatic Virtual Environment (pipx)

When users install with `pipx`:
- ✅ Automatically creates an isolated virtual environment
- ✅ No dependency conflicts with other Python packages
- ✅ Global `jumperless` command available everywhere
- ✅ Easy to update: `pipx upgrade jumperless`
- ✅ Easy to uninstall: `pipx uninstall jumperless`

### Traditional pip Still Works

Users who prefer `pip`:
```bash
python3 -m venv jumperless-env
source jumperless-env/bin/activate
pip install jumperless
jumperless
```

## 📋 Pre-Publishing Checklist

- [ ] Version numbers match in `pyproject.toml` and `bridge.py`
- [ ] README_PYPI.md is up to date
- [ ] LICENSE file is present (GPL-3.0)
- [ ] Test build: `python3 -m build`
- [ ] Check package: `python3 -m twine check dist/*`
- [ ] Test on TestPyPI first
- [ ] Verify installation works
- [ ] Then upload to production PyPI

## 🔧 Troubleshooting

### "File already exists" Error
PyPI doesn't allow re-uploading the same version. Increment version number.

### Import Errors
Make sure `cp JumperlessWokwiBridge.py jumperless_pkg/bridge.py` was run after changes.

### Missing Dependencies
All dependencies from `requirements.txt` are in `pyproject.toml` dependencies section.

## 📚 Additional Resources

- See `PYPI_PUBLISHING_GUIDE.md` for detailed instructions
- Python Packaging Guide: https://packaging.python.org/
- pipx Documentation: https://pipx.pypa.io/

## 🎉 Next Steps

1. Create PyPI account at https://pypi.org/
2. Run `./build_package.sh` to build
3. Upload to TestPyPI to test
4. Upload to PyPI for production
5. Share with users: `pipx install jumperless`

**Your app will now have automatic virtual environment isolation when installed with pipx!**

