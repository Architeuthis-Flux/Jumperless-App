# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Get the current directory
current_dir = Path.cwd()

# Platform-specific settings
if sys.platform == 'win32':
    icon_file = current_dir / 'assets' / 'icons' / 'icon.ico'
    console = False
    name = 'JumperlessWokwiBridge.exe'
elif sys.platform == 'darwin':
    icon_file = current_dir / 'assets' / 'icons' / 'icon.icns'
    console = False
    name = 'JumperlessWokwiBridge'
else:  # Linux
    icon_file = current_dir / 'assets' / 'icons' / 'icon.png'
    console = False
    name = 'JumperlessWokwiBridge'

# Check if icon file exists
if not icon_file.exists():
    print(f"Warning: Icon file not found: {icon_file}")
    icon_file = None

# Data files to include
datas = []

# Add assets directory if it exists
assets_dir = current_dir / 'assets'
if assets_dir.exists():
    datas.append((str(assets_dir), 'assets'))

# Add any other data files
if (current_dir / 'requirements.txt').exists():
    datas.append((str(current_dir / 'requirements.txt'), '.'))

a = Analysis(
    ['JumperlessWokwiBridge.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=console,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_file) if icon_file else None,
)

# macOS app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='Jumperless.app',
        icon=str(icon_file) if icon_file else None,
        bundle_identifier='com.jumperless.wokwibridge',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
        },
    ) 