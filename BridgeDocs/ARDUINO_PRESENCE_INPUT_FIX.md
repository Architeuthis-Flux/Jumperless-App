# Arduino Presence Detection and Input Handling Fix

## Issues Fixed

### 1. Arduino Presence Detection Failure
**Problem:** The `check_arduino_presence()` function was failing to detect Arduino even when "Y,Y" response was sent by the Jumperless. The function would always return `(False, False)`, causing unnecessary prompts.

**Root Cause:** The `serial_term_in()` thread continuously reads from the serial port. When `check_arduino_presence()` sent "A?" and waited for response, the `serial_term_in()` thread would consume the "Y,Y" response before `check_arduino_presence()` could read it.

**Solution:** Wrapped the serial communication in `check_arduino_presence()` with `serial_lock`:
```python
with serial_lock:
    # Flush, write, wait, and read - all protected from other threads
    ser.write(b"A?")
    time.sleep(0.4)
    response = ser.read(ser.in_waiting or 100).decode('utf-8', errors='ignore')
```

This ensures `serial_term_in()` cannot read the response while `check_arduino_presence()` is waiting for it.

### 2. Input Prompt Issues
**Problem:** 
- User had to press Enter twice to submit input
- Input "N" was interpreted as "Y" (wrong response)

**Root Cause:** The `handle_interactive_input_simple()` function (called by `serial_term_out()` thread) was running with terminal in raw mode when `interactive_mode = True`. This caused:
1. The interactive handler to consume the first Enter keypress
2. The `input()` call to get an empty string (from buffered data or partial read)
3. Empty string being treated as "Y" by the logic `if user_input == 'Y' or user_input == ''`

**Solution:** Before calling `input()`, temporarily disable interactive mode and restore terminal settings:
```python
old_interactive_state = interactive_mode
if interactive_mode:
    interactive_mode = False
    time.sleep(0.1)  # Let serial_term_out exit interactive handler

# Restore normal terminal settings
if sys.platform != "win32" and 'original_terminal_settings' in globals():
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, original_terminal_settings)

# Flush input buffer
sys.stdin.flush()

# Now input() works correctly
user_input = input().strip().upper()

# Restore states
interactive_mode = old_interactive_state
```

### 3. Debug Output Added
Added clear status messages so users can see what's happening:
```python
safe_print(f"Arduino detection: connected={is_connected}, present={is_present}", Fore.CYAN)
```

When Arduino is detected, it now clearly states:
```
Arduino detection: connected=True, present=True
✓ Arduino detected and ready - proceeding with flash
```

## Testing
Test the fixes by:
1. Loading a Wokwi project with Arduino sketch
2. Verify you see "Arduino detection: connected=True, present=True"
3. Verify flash proceeds without prompt when Arduino is present
4. Disconnect Arduino and try again
5. Verify prompt appears and accepts input correctly (single Enter press)
6. Verify "N" actually skips the flash

## Technical Details

### Serial Lock Usage
The `serial_lock` is a threading.Lock that prevents concurrent access to the serial port. It's used throughout the codebase but was missing from `check_arduino_presence()`.

### Interactive Mode
Interactive mode is used for character-by-character input (like a terminal emulator). When enabled:
- Terminal is set to raw mode (no line buffering)
- `serial_term_out()` calls `handle_interactive_input()` which reads stdin character-by-character
- Must be disabled for `input()` to work correctly

### Thread Safety
Multiple threads interact with serial and stdin:
- `serial_term_in()` - reads from serial port
- `serial_term_out()` - reads from stdin, writes to serial
- `handle_interactive_input_simple()` - character-by-character stdin reading
- Main thread - calls `input()` for prompts

Proper coordination using locks and state flags is essential.

### 4. Empty Sketch Detection
**Problem:** The system would attempt to flash empty Arduino sketches (containing only empty `setup()` and `loop()` functions), wasting time and resources.

**Solution:** Added validation to detect empty sketches by:
1. Removing comments and whitespace from the sketch
2. Checking if only `void setup(){}` and `void loop(){}` remain
3. Returning success without flashing if sketch is empty

```python
# Strip comments and whitespace
stripped_sketch = re.sub(r'//.*?$|/\*.*?\*/', '', sketch_content, flags=re.MULTILINE | re.DOTALL)
stripped_sketch = re.sub(r'\s+', '', stripped_sketch)

# Check for empty pattern
if 'voidsetup(){}' in stripped_sketch and 'voidloop(){}' in stripped_sketch:
    if stripped_sketch.count('{') <= 2:  # Only setup and loop braces
        return True  # Skip flash, not an error
```

### 5. Variable Scope Bug Fix
**Problem:** Exception handler referenced `old_menu_state` and `old_interactive_state` before they were assigned, causing "local variable referenced before assignment" error.

**Solution:** Initialize these variables to `None` before the try block:
```python
old_menu_state = None
old_interactive_state = None

try:
    old_menu_state = menuEntered
    old_interactive_state = interactive_mode
    # ... rest of code
except Exception as e:
    # Safe to reference old_menu_state and old_interactive_state here
    if old_menu_state is not None:
        menuEntered = old_menu_state
```

## Files Modified
- `JumperlessWokwiBridge.py` - check_arduino_presence() and flash_arduino_sketch()

## Related Issues
This fix resolves the issues where:
- Arduino flash would prompt even when Arduino was connected
- User input wasn't properly received during flash prompts
- Double Enter key press was needed for input confirmation
- "local variable referenced before assignment" error in exception handler
- Empty Arduino sketches would trigger unnecessary flash operations

