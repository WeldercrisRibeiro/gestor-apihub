# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\PROJETOS\\INFARMA\\PIT\\gerenciador-apihub\\apihub.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\INFARMA\\APIHUB\\assets\\apihub.ui', 'assets'), ('C:\\INFARMA\\APIHUB\\assets\\apihub-white.ico', 'assets')],
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
    name='gerenciador-apihub.3.2.1',
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
    icon=['C:\\INFARMA\\APIHUB\\assets\\apihub-white.ico'],
)
