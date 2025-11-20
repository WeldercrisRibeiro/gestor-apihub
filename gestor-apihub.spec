# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['C:\\Users\\Weldercris.ribeiro\\Documents\\INFARMA\\PIT\\gestor-apihub\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\INFARMA\\PIT\\assets\\gestor.apihub.ico', 'assets'),('C:\\INFARMA\\PIT\\assets\\apihub.ico', 'assets')],
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
    name='gestor-apihub.1.0.0',
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

    # Ícone do EXE
    icon='C:\\INFARMA\\PIT\\assets\\gestor.apihub.ico',

    # Usa o manifest externo que você criou
    manifest='admin.manifest',

    # Ativa modo Administrador
    uac_admin=True,
)
