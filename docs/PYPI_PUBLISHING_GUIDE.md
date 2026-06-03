# Publishing Jumperless to PyPI

This guide explains how to publish the Jumperless application to PyPI.

## Prerequisites

1. **PyPI Account**: Create accounts on both:
   - [TestPyPI](https://test.pypi.org/account/register/) - For testing
   - [PyPI](https://pypi.org/account/register/) - For production

2. **API Tokens**: Generate API tokens for both TestPyPI and PyPI:
   - Go to Account Settings → API tokens
   - Click "Add API token"
   - Set scope to "Entire account" (or specific project after first upload)
   - Save the token securely (you can't see it again!)

3. **Install Build Tools**:
   ```bash
   pip install --upgrade build twine
   ```

## Publishing Steps

### 1. Update Version Number

Edit the version in both files:
- `pyproject.toml` (line with `version = "..."`)
- `jumperless_pkg/bridge.py` (line with `App_Version = "..."`)

Make sure they match!

### 2. Build the Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build the package
python -m build
```

This creates two files in `dist/`:
- `jumperless-X.X.X.tar.gz` (source distribution)
- `jumperless-X.X.X-py3-none-any.whl` (wheel distribution)

### 3. Test on TestPyPI First

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your TestPyPI API token (starts with `pypi-`)

### 4. Test Installation from TestPyPI

```bash
# Test with pipx (recommended)
pipx install --index-url https://test.pypi.org/simple/ jumperless

# Or test with pip in a venv
python -m venv test-env
source test-env/bin/activate
pip install --index-url https://test.pypi.org/simple/ jumperless

# Run the app to verify
jumperless

# Cleanup
deactivate
rm -rf test-env
pipx uninstall jumperless
```

### 5. Upload to Production PyPI

Once testing is successful:

```bash
# Upload to PyPI
python -m twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your PyPI API token

### 6. Verify Installation

```bash
# Install from PyPI
pipx install jumperless

# Run the app
jumperless
```

## Using .pypirc for Authentication

Instead of entering credentials each time, create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PYPI_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

**Security**: Set proper permissions: `chmod 600 ~/.pypirc`

## Quick Reference Commands

```bash
# Full workflow
rm -rf dist/ build/ *.egg-info
python -m build
python -m twine upload --repository testpypi dist/*  # Test first
python -m twine upload dist/*                         # Then production

# Check package without uploading
python -m twine check dist/*
```

## Troubleshooting

### "File already exists" Error

PyPI doesn't allow re-uploading the same version. You must increment the version number in `pyproject.toml`.

### Import Errors After Installation

Make sure:
1. Package name is `jumperless_pkg` in the code
2. Entry point in `pyproject.toml` uses `jumperless_pkg.cli:main`
3. All dependencies are listed in `pyproject.toml`

### Missing Assets

Ensure `MANIFEST.in` includes all necessary asset files and that `include-package-data = true` is set in `pyproject.toml`.

## Recommended Installation Methods for Users

### Best: pipx (Automatic Isolation)
```bash
pipx install jumperless
```
- ✅ Automatic virtual environment
- ✅ Global command availability
- ✅ Easy updates
- ✅ No dependency conflicts

### Good: pip with venv (Manual Isolation)
```bash
python -m venv ~/jumperless-venv
source ~/jumperless-venv/bin/activate
pip install jumperless
```

### Not Recommended: System pip
```bash
pip install jumperless  # May cause dependency conflicts
```

## Additional Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [pipx Documentation](https://pipx.pypa.io/)
- [PyPI Help](https://pypi.org/help/)
- [Semantic Versioning](https://semver.org/)

## Version Numbering

Follow semantic versioning: `MAJOR.MINOR.PATCH.BUILD`

- **MAJOR**: Incompatible API changes
- **MINOR**: Add functionality (backwards-compatible)
- **PATCH**: Bug fixes (backwards-compatible)
- **BUILD**: Build number / revision

Current version: 1.1.1.14

