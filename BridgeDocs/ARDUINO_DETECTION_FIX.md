# Arduino Detection and Input Handling Fixes

## Issues Fixed

### 1. Arduino Presence Detection Not Working

**Problem:** App reported "Arduino not detected" even when Jumperless responded with `Y,Y`

**Root Causes:**
- Response was getting mixed with other serial output (menu text, debug messages)
- Timeout was too short (200ms)
- Parsing expected exact "Y,Y" format with no whitespace or extra text

**Solution:**
```python
# 1. Flush serial buffer before checking
if ser.in_waiting > 0:
    ser.read(ser.in_waiting)
    time.sleep(0.05)

# 2. Longer timeout
time.sleep(0.3)  # Increased from 0.2s

# 3. Read more data
response = ser.read(ser.in_waiting or 100)  # Read up to 100 bytes

# 4. Parse line-by-line to find Y,Y even in messy output
lines = response.split('\n')
for line in lines:
    if ',' in line and len(line) <= 10:
        parts = line.split(',')
        if len(parts) == 2:
            is_connected = 'Y' in parts[0].upper()
            is_present = 'Y' in parts[1].upper()
            return (is_connected, is_present)
```

### 2. User Input Not Accepted on macOS

**Problem:** Prompt "Choice (Y/N/A/S):" appeared but input was ignored

**Root Causes:**
- `select.select()` doesn't work in bundled macOS apps or GUI contexts
- stdin might not be a proper file descriptor in packaged apps
- Signal-based approaches (SIGALRM) can conflict with GUI event loops

**Solution:** Use Queue-based threading
```python
import queue

input_queue = queue.Queue()

def get_input():
    try:
        result = input().strip().upper()
        input_queue.put(result)
    except Exception:
        input_queue.put(None)

input_thread = threading.Thread(target=get_input, daemon=True)
input_thread.start()

# Wait up to 10 seconds for input
try:
    user_input = input_queue.get(timeout=10)
except queue.Empty:
    user_input = None  # Timeout
```

**Why this works:**
- ✅ Works in GUI apps and bundled executables
- ✅ Works on all platforms (Windows, macOS, Linux)
- ✅ Proper timeout handling without signals
- ✅ Thread-safe with daemon thread
- ✅ No external dependencies

### 3. Added Debug Output

**Enhancement:** Always show what input was received
```python
safe_print(f"Received input: '{user_input}' (type: {type(user_input).__name__})", Fore.CYAN)
```

This helps diagnose:
- Whether input is being captured
- If there's a type mismatch (str vs bytes)
- If there are hidden characters

## Testing

After these fixes, the Arduino flash flow should work properly:

```
New Arduino sketch for slot 0 - flashing...
Arduino flash started in background for slot 0...
⚠️  Arduino not detected on Jumperless
No Arduino detected. Do you want to:
  [Y] Flash anyway (maybe Arduino is connected differently)
  [N] Skip this flash
  [A] Always flash without asking
  [S] Never flash when Arduino not detected
Choice (Y/N/A/S): S
Received input: 'S' (type: str)
✓ Will skip flashing when Arduino not present
```

**If Arduino IS detected:**
```
New Arduino sketch for slot 0 - flashing...
Arduino flash started in background for slot 0...
Arduino detected and ready
Compiling Arduino sketch...
[flash proceeds normally]
```

## Files Modified

- `JumperlessWokwiBridge.py` - Fixed `check_arduino_presence()` and user input handling

## Related Issues

- macOS bundled apps have limited stdin/stdout access
- GUI frameworks can interfere with signal handlers
- Queue-based threading is the most portable solution

