# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.building.build_main import Analysis, PYZ, EXE

a = Analysis(
    [r'C:\Users\euwel\OneDrive\Documentos\INFARMA\PIT\gerenciador-apihub\apihub.py'],
    pathex=[],
    binaries=[],
    datas=[
        (r'C:\INFARMA\APIHUB\assets\apihub.ui', 'assets'),
        (r'C:\INFARMA\APIHUB\assets\apihub-white.ico', 'assets'),
    ],
    hiddenimports=[],
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
    name='gerenciador-apiHub-3.0.0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r'C:\INFARMA\APIHUB\assets\apihub-white.ico',
)
