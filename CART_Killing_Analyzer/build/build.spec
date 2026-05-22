# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 for CAR-T 杀伤分析工具"""

a = Analysis(
    ['../src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('../resources/icon.ico', 'resources'), ('../resources/icon.png', 'resources')],
    hiddenimports=[
        'matplotlib.backends.backend_tkagg',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.ttk',
        'pandas',
        'pandas._libs',
        'pandas._libs.tslibs',
        'scipy',
        'statsmodels',
        'openpyxl',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib.tests',
        'pandas.tests',
        'numpy.random._examples',
    ],
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
    name='CART_Killing_Analyzer',
    icon='../resources/icon.ico',
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
)
