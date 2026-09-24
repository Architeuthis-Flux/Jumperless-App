#!/usr/bin/env python3
"""
Self-check for the firmware classification in JumperlessWokwiBridge.py.

The bridge is one 7,500-line script with side effects at import, so the two
pure functions are lifted out of its source with ast and exec'd here. Run:
    python3 Scripts/test_firmware_classify.py
"""
import ast
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "JumperlessWokwiBridge.py"
WANT = {"classify_firmware", "og_backport_version_from_tag", "firmware_version_compare"}

tree = ast.parse(SRC.read_text(encoding="utf-8"))
funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in WANT]
assert {f.name for f in funcs} == WANT, f"missing: {WANT - {f.name for f in funcs}}"
ns = {"re": re}
exec(compile(ast.Module(body=funcs, type_ignores=[]), str(SRC), "exec"), ns)
classify = ns["classify_firmware"]
og_version = ns["og_backport_version_from_tag"]
newer_or_same = ns["firmware_version_compare"]

# V5 firmware, as the board reports it and as the app has already cleaned it.
assert classify("5.7.11.3") == "v5"
assert classify("5.7.11.3\r") == "v5"
assert classify("6.0.0.0") == "v5"
# OG running JumperlOS: major 1, four parts.
assert classify("1.7.11.3") == "og_backport"
assert classify("1.7.11.3.") == "og_backport"
# Original OG firmware: three parts.
assert classify("1.3.23") == "og_original"
assert classify("1.3") == "og_original"
# Garbage never selects the JumperlOS feed.
assert classify("") == "og_original"
assert classify("unknown") == "og_original"
assert classify(None) == "og_original"

# The OG asset on a JumperlOS release is 1.<tag tail>, as release.yml derives it.
assert og_version("5.7.11.3") == "1.7.11.3"
assert og_version("v5.7.11.3") == "1.7.11.3"
assert og_version("5.8.0") == "1.8.0"

# check_if_fw_is_old() offers an update when the latest tag is newer than the
# board. A three-part tag must compare as a version, not as a digit string.
assert newer_or_same("1.8.0", "1.7.11.2") is True
assert newer_or_same("1.7.11.2", "1.8.0") is False
assert newer_or_same("1.7.11.3", "1.7.11.3") is True
assert newer_or_same("1.7.11.2", "1.7.11.3") is False

print("firmware classify self-check: OK")
