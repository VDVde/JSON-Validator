# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for VDV463 Validator
Builds a portable Windows executable with all dependencies bundled.
"""

import sys
from pathlib import Path

# Get the project root directory
project_root = Path(SPECPATH)

block_cipher = None

# Data files to include
datas = [
    # Include the UI folder
    (str(project_root / 'UI'), 'UI'),
    # Include schemas
    (str(project_root / 'schemas'), 'schemas'),
    # Include rules
    (str(project_root / 'rules'), 'rules'),
    # Include media (logo, icons)
    (str(project_root / 'media'), 'media'),
    # Include pyproject.toml for version info
    (str(project_root / 'pyproject.toml'), '.'),
]

# Hidden imports for PySide6
hidden_imports = [
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
]

a = Analysis(
    [str(project_root / 'UI' / 'main_ui.py')],
    pathex=[
        str(project_root / 'src'),
        str(project_root / 'UI'),
    ],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VDV463Validator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI application, no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Icon will be set if logo.ico exists (created during build)
    icon=str(project_root / 'media' / 'logo.ico') if (project_root / 'media' / 'logo.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)
