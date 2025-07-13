#!/usr/bin/env python3
"""
Create Windows version info file for PyInstaller
"""

import os
import sys
from pathlib import Path

def get_version():
    """Get version from various sources"""
    
    # Try to get from git tag
    try:
        import subprocess
        result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            if version.startswith('v'):
                version = version[1:]  # Remove 'v' prefix
            return version
    except:
        pass
    
    # Try to get from pyproject.toml
    try:
        import toml
        with open('pyproject.toml', 'r') as f:
            data = toml.load(f)
            return data.get('project', {}).get('version', '1.0.0')
    except:
        pass
    
    # Try to get from setup.py or __init__.py
    try:
        with open('JumperlessWokwiBridge.py', 'r') as f:
            content = f.read()
            import re
            match = re.search(r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]', content)
            if match:
                return match.group(1)
    except:
        pass
    
    # Default version
    return "1.0.0"

def create_version_info():
    """Create Windows version info file"""
    
    version = get_version()
    version_parts = version.split('.')
    
    # Ensure we have 4 parts for Windows version
    while len(version_parts) < 4:
        version_parts.append('0')
    
    version_tuple = tuple(int(part) for part in version_parts[:4])
    
    version_info_content = f'''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers={version_tuple},
    prodvers={version_tuple},
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x4,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
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
            StringStruct(u'InternalName', u'JumperlessWokwiBridge'),
            StringStruct(u'LegalCopyright', u'© 2025 Jumperless Project'),
            StringStruct(u'OriginalFilename', u'JumperlessWokwiBridge.exe'),
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
    
    # Write version info file
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info_content)
    
    print(f"✅ Created version_info.txt with version {version}")

if __name__ == "__main__":
    create_version_info() 