# -*- mode: python ; coding: utf-8 -*-
import sys
import os
import platform

# Platform-specific settings
is_windows = platform.system() == 'Windows'
is_macos = platform.system() == 'Darwin'
is_linux = platform.system() == 'Linux'

# Platform-specific icon file
icon_file = None
if is_windows:
    # Windows icon file (.ico)
    icon_file = 'assets/shotpipe.ico' if os.path.exists('assets/shotpipe.ico') else None
elif is_macos:
    # macOS icon file (.icns)
    icon_file = 'assets/shotpipe.icns' if os.path.exists('assets/shotpipe.icns') else None

# Hidden imports that might be needed
hidden_imports = [
    'PyQt5.QtCore',
    'PyQt5.QtGui', 
    'PyQt5.QtWidgets',
    'shotgun_api3',
    'yaml',
    'dotenv',
    'PIL',
    'PIL.Image',
    'exiftool',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('shotpipe', 'shotpipe'),
        ('vendor', 'vendor'),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ShotPipe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=is_macos,  # Enable on macOS for proper drag-and-drop support
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

# macOS-specific app bundle
if is_macos:
    app = BUNDLE(
        exe,
        name='ShotPipe.app',
        icon=icon_file,
        bundle_identifier='com.shotpipe.app',
        info_plist={
            'CFBundleName': 'ShotPipe',
            'CFBundleDisplayName': 'ShotPipe',
            'CFBundleGetInfoString': 'ShotPipe - AI Generated File to Shotgrid Automation',
            'CFBundleIdentifier': 'com.shotpipe.app',
            'CFBundleVersion': '1.3.0',
            'CFBundleShortVersionString': '1.3.0',
            'NSHighResolutionCapable': 'True',
            'LSApplicationCategoryType': 'public.app-category.productivity',
            'NSRequiresAquaSystemAppearance': 'False',  # Support dark mode
        },
    )
