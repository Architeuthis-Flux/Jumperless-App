# How the Jumperless PyPI Package Works

## 🔄 Installation Flow

### With pipx (Recommended - Automatic Isolation)

```
User runs: pipx install jumperless
              ↓
pipx creates isolated venv at ~/.local/pipx/venvs/jumperless/
              ↓
pipx runs: pip install jumperless (inside the venv)
              ↓
pip downloads from PyPI:
  - jumperless-1.1.1.14-py3-none-any.whl
  - Installs to venv: jumperless_pkg/
              ↓
pip installs all dependencies automatically:
  - beautifulsoup4, packaging, psutil, pyduinocli, pyserial, requests, colorama
  - Windows only: pywin32, pynput
              ↓
pip creates console script entry point
  from pyproject.toml: jumperless = "jumperless_pkg.cli:main"
              ↓
pipx creates global symlink:
  ~/.local/bin/jumperless → venv's jumperless script
              ↓
User can run: jumperless (from anywhere!)
              ↓
Runs: jumperless_pkg.cli.main()
              ↓
Which calls: jumperless_pkg.bridge.main()
              ↓
Your JumperlessWokwiBridge app starts! 🎉
```

**Result:**
- ✅ Completely isolated from other Python packages
- ✅ No manual venv creation needed
- ✅ Command available globally
- ✅ Dependencies can't conflict with other apps

### With pip (Manual Isolation)

```
User runs: python3 -m venv jumperless-env
User runs: source jumperless-env/bin/activate
User runs: pip install jumperless
              ↓
pip downloads from PyPI and installs to venv
              ↓
User runs: jumperless
              ↓
Your app starts! 🎉
```

**Note:** User must activate venv each time they want to run the app.

## 📦 Package Structure Explained

### What Gets Uploaded to PyPI

```
jumperless-1.1.1.14.tar.gz (source distribution)
├── jumperless_pkg/
│   ├── __init__.py          # Package version and metadata
│   ├── cli.py               # Entry point wrapper
│   ├── bridge.py            # Your full app (5700+ lines)
│   └── assets/              # Icons, configs, examples
│       ├── avrdudeCustom.conf
│       ├── example_sketch.ino
│       └── icons/*.png
├── pyproject.toml           # Tells pip how to install
├── README_PYPI.md          # Shown on PyPI website
└── LICENSE                  # GPL-3.0

jumperless-1.1.1.14-py3-none-any.whl (wheel distribution)
└── (Same files, pre-built for faster installation)
```

### How Files Are Used

**During Installation:**
- `pyproject.toml` → Tells pip what to install, dependencies, entry points
- `README_PYPI.md` → Displayed on https://pypi.org/project/jumperless/
- `LICENSE` → Legal terms
- `jumperless_pkg/*` → Installed to user's venv/system

**After Installation:**
- `jumperless_pkg/cli.py:main()` → Called when user runs `jumperless` command
- `jumperless_pkg/bridge.py:main()` → Your actual application
- `jumperless_pkg/assets/*` → Available at runtime via pkg_resources

## 🎯 Entry Point Magic

### In pyproject.toml:
```toml
[project.scripts]
jumperless = "jumperless_pkg.cli:main"
```

This tells pip/pipx to create a script called `jumperless` that:
1. Activates the correct Python environment
2. Imports `jumperless_pkg.cli`
3. Calls the `main()` function

### What Gets Created

After installation, pip creates a script like this:

**On Unix/Mac** (`~/.local/bin/jumperless`):
```python
#!/path/to/venv/bin/python3
# -*- coding: utf-8 -*-
import re
import sys
from jumperless_pkg.cli import main

if __name__ == '__main__':
    sys.exit(main())
```

**On Windows** (`Scripts\jumperless.exe`):
- A Windows executable that does the same thing

## 🔍 Dependency Resolution

### Defined in pyproject.toml:

```toml
dependencies = [
    "beautifulsoup4>=4.13.4",
    "packaging>=24.1",
    "psutil>=5.9.8",
    "pyduinocli>=0.35.0",
    "pyserial>=3.5",
    "requests>=2.32.3",
    "colorama>=0.4.6",
    "pywin32>=306; platform_system == 'Windows'",
    "pynput; platform_system == 'Windows'",
]
```

### What Happens:
1. pip reads the dependencies
2. Downloads each package from PyPI
3. Installs them in the same venv
4. Handles version constraints automatically
5. Platform-specific deps (pywin32, pynput) only on Windows

## 🌍 Cross-Platform Support

### How It Works:

**Platform Detection:**
```toml
"pywin32>=306; platform_system == 'Windows'"
```
- On Windows: pip installs pywin32
- On Mac/Linux: pip skips it

**In Your Code:**
```python
if sys.platform == "win32":
    import win32api
    WIN32_AVAILABLE = True
```

**Result:** Same package works everywhere!

## 🔄 Update Flow for Maintainers

```
1. Edit JumperlessWokwiBridge.py
   └─ Make your changes
        ↓
2. Update versions (BOTH files!)
   ├─ pyproject.toml: version = "1.1.1.15"
   └─ JumperlessWokwiBridge.py: App_Version = "1.1.1.15"
        ↓
3. Copy to package
   └─ cp JumperlessWokwiBridge.py jumperless_pkg/bridge.py
        ↓
4. Build
   └─ ./build_package.sh
        ↓
5. Publish
   └─ python3 -m twine upload dist/*
        ↓
6. Users update
   └─ pipx upgrade jumperless
```

## 📊 File Size Breakdown

- **Source** (jumperless-1.1.1.14.tar.gz): 24MB
  - Includes: Source code, assets, metadata, README
  - Used by: pip when building from source

- **Wheel** (jumperless-1.1.1.14-py3-none-any.whl): 12MB
  - Pre-built, ready to install
  - Faster installation
  - Used by: pip/pipx for quick installs

**Why both?**
- Wheel: Fast installation (preferred)
- Source: Compatibility, inspection, building on any platform

## 🎨 The pipx Advantage

### Without pipx (Traditional):
```
User has Python + many packages installed globally
  ├── requests 2.28.0 (for other app)
  ├── beautifulsoup4 4.11.0 (for other app)
  └── ... other packages

User installs jumperless:
  → pip install jumperless
  → Needs requests 2.32.3 (conflict!)
  → Upgrades global requests
  → Breaks other app 💥
```

### With pipx (Modern):
```
User's global Python
  ├── requests 2.28.0 (for other app)
  └── ... other packages

User installs with pipx:
  → pipx install jumperless
  → Creates ~/.local/pipx/venvs/jumperless/
      ├── requests 2.32.3 ✅
      ├── beautifulsoup4 4.13.4 ✅
      └── ... all deps isolated ✅
  → Links command: ~/.local/bin/jumperless
  
User's global Python unchanged!
Other app still works! ✅
Jumperless has exact deps it needs! ✅
```

## 🔐 Security: API Tokens

### Why Tokens Instead of Passwords?

- ✅ Can be revoked without changing password
- ✅ Scope limited to package uploads
- ✅ Can have multiple tokens for different purposes
- ✅ Safer for automation

### Token Format:
```
pypi-AgEIcHlwaS5vcmcCJGFiY2RlZi0xMjM0LTU2NzgtOTBhYi1jZGVmMTIzNDU2Nzg...
```

### Using in .pypirc:
```ini
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcCJGFiY2RlZi0xMjM0LTU2NzgtOTBhYi1jZGVmMTIzNDU2Nzg...
```

## 📖 PyPI Package Page

After publishing, your package page will show:

**URL:** https://pypi.org/project/jumperless/

**Content:**
- Package name and version
- Description (from pyproject.toml)
- README_PYPI.md contents (rendered)
- Installation instructions
- Dependencies list
- Supported platforms
- License
- Links (homepage, repo, docs, issues)
- Download statistics
- Version history

## 🎓 Understanding the Parts

### pyproject.toml Sections:

1. **[build-system]** - How to build the package
2. **[project]** - Metadata (name, version, description, dependencies)
3. **[project.scripts]** - Creates console commands
4. **[tool.setuptools]** - Package finding and data files

### Why Two Copies of the App?

1. **JumperlessWokwiBridge.py** - Your working copy
   - This is what you edit
   - Run directly: `python JumperlessWokwiBridge.py`
   - Version controlled in git

2. **jumperless_pkg/bridge.py** - Package copy
   - Snapshot for PyPI distribution
   - Gets installed to user's system
   - Only updated when you copy from #1

**Workflow:** Edit #1 → Copy to #2 → Build → Publish

## 💻 What's Installed on User's System

### With pipx:
```
~/.local/pipx/venvs/jumperless/
├── bin/
│   ├── python3 → /usr/bin/python3
│   └── jumperless → wrapper script
├── lib/python3.x/site-packages/
│   ├── jumperless_pkg/
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── bridge.py
│   │   └── assets/
│   ├── beautifulsoup4/
│   ├── packaging/
│   ├── psutil/
│   └── ... (all dependencies)
└── ...

~/.local/bin/jumperless → symlink to venv's script
```

### With pip (in venv):
```
jumperless-env/
├── bin/
│   ├── python3
│   └── jumperless
├── lib/python3.x/site-packages/
│   ├── jumperless_pkg/
│   └── ... (dependencies)
└── ...
```

## 🎉 The End Result

### For Users:
```bash
# Install (one command)
pipx install jumperless

# Run (from anywhere)
jumperless

# Update (one command)
pipx upgrade jumperless

# Remove (one command)
pipx uninstall jumperless
```

**Simple, clean, professional!**

### For You (Maintainer):
```bash
# Update app
edit JumperlessWokwiBridge.py

# Update version numbers (2 files)
# Copy and publish
cp JumperlessWokwiBridge.py jumperless_pkg/bridge.py
./publish_to_pypi.sh

# Users get the update
pipx upgrade jumperless
```

**Streamlined workflow!**

---

## 🚀 Ready to Publish?

See: `PYPI_QUICKSTART.md` or run `./publish_to_pypi.sh`

