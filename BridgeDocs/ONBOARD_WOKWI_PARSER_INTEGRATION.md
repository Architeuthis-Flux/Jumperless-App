# Onboard Wokwi Parser Integration

## Overview
Modified the Python bridge to take advantage of the onboard Wokwi parser available in firmware version 5.4.0.3+ for Jumperless V5 boards. This allows the device to receive raw Wokwi diagram.json data and parse it locally, preserving color information and other metadata that was previously lost in the Python-side parsing.

## Changes Made

### 1. Version Comparison Function (`firmware_version_compare`)
**Location:** Line 4555-4579

Added a utility function to compare firmware version strings:
```python
def firmware_version_compare(current_version, target_version):
    """
    Compare two firmware version strings.
    Returns True if current_version >= target_version
    Example: firmware_version_compare("5.4.0.3", "5.4.0.3") -> True
    """
```

**Reasoning:**
- Robust version comparison handles variable-length version strings (e.g., "5.4.0" vs "5.4.0.3")
- Pads shorter versions with zeros for proper comparison
- Returns False on parse errors (assumes old version as fail-safe)
- Allows seamless backward compatibility with older firmware

### 2. Conditional Parser Selection
**Location:** Line 4789-4880

Modified the Wokwi update loop to detect firmware capability and choose appropriate method:

**Detection Logic:**
```python
use_onboard_parser = (jumperlessV5 and 
                      currentString != 'unknown' and 
                      firmware_version_compare(currentString, "5.4.0.3"))
```

**Change Detection:**
The hashing strategy differs based on parser capability:

**New Method (Full Diagram Hash):**
```python
# Hash the entire diagram including colors, text, parts
current_diagram_hash = json.dumps(wokwi_data, sort_keys=True, separators=(',', ':'))
```
This detects changes to:
- Wire colors (connection[].color)
- Component colors (parts[].attrs.color)
- Text labels (text[] array for rail voltages)
- Any other diagram metadata

**Old Method (Endpoints Only Hash):**
```python
# Hash only connection endpoints (backward compatibility)
normalized_connections = [(sorted([conn[0], conn[1]])) for conn in connections]
current_diagram_hash = str(sorted(normalized_connections))
```
This only detects changes to connection endpoints, not colors or metadata.

**Conditions Required:**
1. Must be Jumperless V5 hardware (`jumperlessV5 == True`)
2. Firmware version must be known (`currentString != 'unknown'`)
3. Firmware version must be >= 5.4.0.3

**New Method (Onboard Parser):**
- Format: `W [slot] {json}`
- Sends complete Wokwi diagram.json as compact JSON string
- Preserves all metadata including:
  - Wire colors
  - Component colors  
  - Text labels (for rail voltages)
  - Full connection details
- Example: `W 0 {"connections":[["bb1:1t.1","bb1:2t.1"],...],"parts":[...]}`

**Old Method (Python Parser):**
- Format: `o Slot [slot] f { connections }`
- Sends only parsed connection pairs
- Loses color and metadata information
- Example: `o Slot 0 f { 1-2, 3-4, }`

### 3. Debug Output
Added debug messages when using onboard parser:
```python
if debugWokwi and use_onboard_parser:
    safe_print(f"Using onboard Wokwi parser (firmware {currentString})", Fore.CYAN)
```

User sees clear indication of which parsing method is active:
- "Updated slot X (onboard parser)" - using new method
- "Updated slot X" - using old method

## Benefits

### For Users
1. **Color Preservation:** Wire and component colors from Wokwi are now preserved and displayed on the hardware
2. **Rail Voltages:** Text labels in Wokwi (e.g., "5V", "3.3V") are parsed and applied to power rails
3. **Better Fidelity:** Complete Wokwi state is transferred to hardware without information loss
4. **Live Color Updates:** Changing a wire color in Wokwi now triggers an immediate update to the hardware (previously would not resend)

### For Developers
1. **Single Source of Truth:** Parsing logic exists only on the firmware side
2. **Easier Updates:** Parser improvements benefit both interactive and app-based workflows
3. **Reduced Duplication:** No need to maintain parallel parsing logic in Python and C++

### For Backward Compatibility
1. **Seamless Fallback:** Older firmware automatically uses old method
2. **No Breaking Changes:** Users with older firmware continue to work without issues
3. **Gradual Migration:** Users upgrade firmware at their own pace

## Implementation Details

### Command Format
The onboard parser expects the `W` command format documented in `SingleCharCommands.cpp`:
- `W [slot]` followed by JSON paste
- The parser detects if data is coming from the app (immediate paste) vs interactive user (prompt for paste)
- Supports both file-based (`W filename.json`) and paste-based input

### JSON Handling
- Uses Python's `json.dumps()` with compact separators `(',', ':')` to minimize data size
- Full `wokwi_data` object is sent (connections, parts, text labels, etc.)
- Device-side parser in `WokwiParser.cpp` handles JSON parsing without external libraries

### Error Handling
- Serial write errors are caught and logged
- Falls back to old method if version comparison fails
- Empty projects are skipped (no connections) regardless of method

## Testing Recommendations

1. **Version Detection:**
   - Verify `currentString` is correctly parsed from firmware response
   - Test with various version formats (5.4.0.3, 5.4.1, 5.5.0, etc.)

2. **Backward Compatibility:**
   - Test with firmware < 5.4.0.3 (should use old method)
   - Test with firmware >= 5.4.0.3 (should use new method)
   - Test with Jumperless V4 (should always use old method)

3. **Functional Testing:**
   - Verify wire colors are preserved in new method
   - Verify rail voltages are correctly applied
   - Verify connection accuracy matches old method
   - Test with complex diagrams (many connections, colors, labels)

4. **Debug Mode:**
   - Enable `debugWokwi` to see which parser is active
   - Verify JSON size is reasonable (typically < 32KB)
   - Check for any serialization errors

## Related Files

### Python Bridge
- `JumperlessWokwiBridge.py` - Main bridge (modified)
- Lines 4555-4579: Version comparison function
- Lines 4789-4868: Conditional parser selection

### Firmware
- `src/WokwiParser.cpp` - Onboard JSON parser
- `src/WokwiParser.h` - Parser interface
- `src/SingleCharCommands.cpp` - W command handler (lines 759-1049)
- `src/Colors.cpp` - Color mapping for wires and components

## Future Improvements

1. **Compression:** Consider gzip compression for very large diagrams (>10KB)
2. **Chunking:** For diagrams >32KB, implement multi-packet transmission
3. **Validation:** Add JSON schema validation on device side
4. **Caching:** Store parsed state to avoid re-parsing unchanged diagrams
5. **Progress Feedback:** Show parsing progress for large diagrams

## Version History

- **2024-10-14:** Initial implementation - onboard parser support for firmware >= 5.4.0.3
  - Added `firmware_version_compare()` function for robust version detection
  - Implemented conditional parser selection based on firmware capability
  - **Fixed:** Change detection now includes full diagram hash (colors, text, parts) for onboard parser
  - Maintains backward compatibility with old method (endpoint-only hash) for older firmware

