# File Path Resolution Fix

## Problem
The Python bridge app was unable to locate `savedProjects.txt` and `slotAssignments.txt` when run from a different working directory than the script's location. Users would see:

```
No saved projects found.
```

Even though the files existed in the correct location.

## Root Cause
The file paths were defined as relative strings:
```python
slotAssignmentsFile = "JumperlessFiles/slotAssignments.txt"
savedProjectsFile = "JumperlessFiles/savedProjects.txt"
```

These paths only work if:
1. The current working directory (`os.getcwd()`) is the script's directory
2. The user runs the script from that directory

If the user runs the script from elsewhere (e.g., `python ~/path/to/JumperlessWokwiBridge.py`), the relative paths fail because they're resolved relative to the current working directory, not the script's location.

## Solution

### 1. Absolute Path Resolution (Lines 427-438)
Changed the file path definitions to compute absolute paths based on the script/executable location:

```python
# File paths - use absolute paths based on script/executable location
# This ensures the files are found regardless of working directory
# For PyInstaller, use the directory of the executable, not the temp extraction dir
if getattr(sys, 'frozen', False):
    # Running as compiled executable (PyInstaller)
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    # Running as Python script
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

slotAssignmentsFile = os.path.join(SCRIPT_DIR, "JumperlessFiles", "slotAssignments.txt")
savedProjectsFile = os.path.join(SCRIPT_DIR, "JumperlessFiles", "savedProjects.txt")
```

**Key Logic:**
- **PyInstaller detection:** Uses `sys.frozen` attribute to detect if running as compiled executable
- **Executable mode:** Uses `sys.executable` to get the executable's directory
- **Script mode:** Uses `__file__` to get the script's directory
- **Path construction:** Uses `os.path.join()` for cross-platform compatibility

### 2. Startup Message (Line 4680)
Added a visible message showing where the app is looking for data files:

```python
# Show where data files are located (helpful for debugging path issues)
safe_print(f"Data directory: {SCRIPT_DIR}/JumperlessFiles/", Fore.BLUE)
```

This appears during app startup:
```
Data directory: /Users/username/Documents/GitHub/Jumperless-App/JumperlessFiles/
```

**Benefit:** Users can immediately see if the path is correct, making diagnosis trivial.

### 3. Debug Output (Lines 2278-2283)
Enhanced error messages to show full paths when `debugWokwi` is enabled:

```python
except FileNotFoundError:
    safe_print("No saved projects found.", Fore.YELLOW)
    if debugWokwi:
        safe_print(f"  (Looked for: {savedProjectsFile})", Fore.BLUE)
except Exception as e:
    safe_print(f"Error reading saved projects: {e}", Fore.RED)
    if debugWokwi:
        safe_print(f"  (File path: {savedProjectsFile})", Fore.BLUE)
```

When `debug` is enabled in the menu, error messages now include the full path being searched.

## Why This Approach?

### Current Working Directory vs Script Directory
There are two common approaches to file paths in Python applications:

**Approach 1: Relative to CWD (Original, Broken)**
```python
path = "JumperlessFiles/file.txt"
# Resolves relative to os.getcwd()
```
- ✅ Simple
- ❌ Breaks when run from different directory
- ❌ Confusing for users

**Approach 2: Relative to Script (Our Fix)**
```python
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(SCRIPT_DIR, "JumperlessFiles", "file.txt")
# Resolves relative to script location
```
- ✅ Works from any directory
- ✅ Intuitive (files live next to script)
- ✅ Compatible with PyInstaller
- ✅ Cross-platform

### PyInstaller Consideration
When frozen with PyInstaller:
- `__file__` points to the temporary extraction directory (`sys._MEIPASS`)
- User data files should NOT be in the temp directory
- Solution: Use `sys.executable` to get the actual executable's directory
- User data files live next to the `.exe` or `.app`

This ensures that:
1. **Development:** Files are in `Jumperless-App/JumperlessFiles/`
2. **Packaged:** Files are next to the executable (e.g., `Jumperless.app/Contents/MacOS/JumperlessFiles/`)

## Testing Recommendations

### 1. Different Working Directories
```bash
# From script directory (should work)
cd ~/Documents/GitHub/Jumperless-App
python JumperlessWokwiBridge.py

# From parent directory (should now work)
cd ~/Documents/GitHub
python Jumperless-App/JumperlessWokwiBridge.py

# From home directory (should now work)
cd ~
python Documents/GitHub/Jumperless-App/JumperlessWokwiBridge.py
```

### 2. Verify Startup Message
Check that "Data directory:" shows the correct absolute path.

### 3. Test Saved Projects
```
menu → slots → [choose slot] → link/path
```
Should show saved projects list or create the file if it doesn't exist.

### 4. Debug Mode
```
menu → debug → [enable]
menu → slots
```
If file not found, should show full path in debug output.

### 5. Packaged Executable
After building with PyInstaller:
```bash
# macOS
./dist/Jumperless.app/Contents/MacOS/Jumperless

# Verify JumperlessFiles/ is created next to executable
ls ./dist/Jumperless.app/Contents/MacOS/JumperlessFiles/
```

## Related Issues

### Existing `resource_path()` Function
The codebase already had a `resource_path()` function (line 451-454):
```python
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)
```

**Why Not Use This?**
- This function uses `sys._MEIPASS` for PyInstaller, which points to the **temporary extraction directory**
- User data files (saved projects, slot assignments) should NOT be in the temp directory
- They need to persist across runs and be user-accessible
- Our fix uses `sys.executable` instead, placing files next to the executable

**When to Use `resource_path()`:**
- For **bundled assets** (icons, fonts, etc.) that are read-only and packaged with the app
- These files are extracted to `_MEIPASS` and accessed from there

**When to Use `SCRIPT_DIR`:**
- For **user data files** that persist across runs
- For **configuration files** that users might edit
- For **log files** or other runtime-generated content

## Impact

### Before
```
$ cd ~
$ python Documents/GitHub/Jumperless-App/JumperlessWokwiBridge.py
...
menu → slots → [choose slot]
No saved projects found.  ❌ (file exists but can't be found)
```

### After
```
$ cd ~
$ python Documents/GitHub/Jumperless-App/JumperlessWokwiBridge.py
...
Data directory: /Users/username/Documents/GitHub/Jumperless-App/JumperlessFiles/
...
menu → slots → [choose slot]
Saved Projects:  ✅
1: My Blinky Project    https://wokwi.com/projects/123456
```

## Files Modified

1. **JumperlessWokwiBridge.py**
   - Lines 427-438: Absolute path resolution
   - Line 4680: Startup message showing data directory
   - Lines 2278-2283: Enhanced error messages with full paths

## Version History

- **2024-10-14:** Fixed file path resolution for `savedProjects.txt` and `slotAssignments.txt`
  - Changed from relative to absolute paths based on script/executable location
  - Added PyInstaller support using `sys.frozen` and `sys.executable`
  - Added startup message showing data directory location
  - Enhanced error messages with full paths when debug mode enabled

