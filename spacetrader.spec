# PyInstaller spec for Space Trader.
#
# Build with:
#   ./venv/bin/pyinstaller spacetrader.spec
#
# Produces a windowed (no console) standalone build:
#   - macOS: dist/Space Trader.app
#   - Windows: dist/Space Trader/Space Trader.exe
#   - Linux:   dist/Space Trader/Space Trader
#
# Settings, saves, and logs are written to an OS-appropriate per-user
# data directory (see src/paths.py), not next to the executable, since
# the bundle itself may be read-only (a signed macOS .app) or installed
# somewhere requiring admin rights to write to (Program Files).
#
# No custom icon is set yet - add one (.icns for macOS, .ico for
# Windows) and pass it as `icon=` below when branding art is ready.

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

# onedir build: the executable references binaries/data alongside it rather
# than unpacking a single file to a temp dir on every launch (faster start,
# and the only sensible option for a macOS .app bundle per PyInstaller).
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Space Trader',
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
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Space Trader',
)

app = BUNDLE(
    coll,
    name='Space Trader.app',
    icon=None,
    bundle_identifier='com.spacetrader.game',
    info_plist={
        'CFBundleName': 'Space Trader',
        'CFBundleDisplayName': 'Space Trader',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    },
)
