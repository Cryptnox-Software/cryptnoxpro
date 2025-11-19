# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['cryptnox_cli\\main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('cryptnox_cli', 'cryptnox_cli')
    ],
    hiddenimports=[
        'lazy_import',
        'six',
        'winsdk',
        'winsdk.windows',
        'winsdk.windows.security.credentials',
        'winsdk.windows.security.cryptography',
        'nfc',
        'smartcard',
        'multiprocessing',
        'tabulate',
        'coincurve',
        'eth_keys',
        'requests',
        'urllib3',
        'websockets',
        'aiohttp',
        'botocore',
        'awscrt'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['build'],
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
    name='CryptnoxCLI-1.0.0-setup',
    icon='cryptnox.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=False,
)
