#!/usr/bin/env python3
"""Create Windows version info file for PyInstaller."""

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from read_version import read_version


def create_version_info():
    """Create Windows version info file."""
    version = read_version()
    version_parts = version.split(".")

    while len(version_parts) < 4:
        version_parts.append("0")

    version_tuple = tuple(int(part) for part in version_parts[:4])

    version_info_content = f'''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_tuple},
    prodvers={version_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [
            StringStruct(u'CompanyName', u'Jumperless Project'),
            StringStruct(u'FileDescription', u'Jumperless Wokwi Bridge'),
            StringStruct(u'FileVersion', u'{version}'),
            StringStruct(u'InternalName', u'Jumperless'),
            StringStruct(u'LegalCopyright', u'© 2025 Jumperless Project'),
            StringStruct(u'OriginalFilename', u'Jumperless.exe'),
            StringStruct(u'ProductName', u'Jumperless Wokwi Bridge'),
            StringStruct(u'ProductVersion', u'{version}'),
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''

    with open(ROOT / "version_info.txt", "w", encoding="utf-8") as handle:
        handle.write(version_info_content)

    print(f"Created version_info.txt with version {version}")


if __name__ == "__main__":
    create_version_info()
