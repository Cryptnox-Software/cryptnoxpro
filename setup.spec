# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Find lazy_import VERSION file
import lazy_import
lazy_import_version = os.path.join(os.path.dirname(lazy_import.__file__), 'VERSION')

a = Analysis(
    ['cryptnox_cli\\main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Only include non-Python data files
        ('cryptnox_cli\\contract_abi\\*.json', 'cryptnox_cli\\contract_abi'),
        (lazy_import_version, 'lazy_import')
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
        'awscrt',
        # Dynamically imported user_keys submodules
        'cryptnox_cli.command.user_keys.aws_kms',
        'cryptnox_cli.command.user_keys.hello',
        'cryptnox_cli.command.user_keys.piv'
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
