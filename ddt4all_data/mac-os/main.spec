# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['../../main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../../ddt4all_data/icons', 'ddt4all_data/icons'),
        ('../../ddt4all_data/locale', 'ddt4all_data/locale'),
        ('../../ddt4all_data/projects.json', 'ddt4all_data'),
        ('../../ddt4all_data/*.qss', 'ddt4all_data'),
        ('../../ddtplugins/*.py', 'ddtplugins'),
        ('../../*.py', '.'),
        ('../../*.zip', '.')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DDT4ALL',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DDT4ALL',
)
app = BUNDLE(
    coll,
    name='DDT4ALL.app',
    icon='../icons/obd.icns',
    bundle_identifier='com.github.cedric.ddt4all',
)
