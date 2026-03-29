from __future__ import annotations

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


# PyInstaller executes spec files without defining __file__.
PROJECT_ROOT = Path.cwd()

datas = [
    (str(PROJECT_ROOT / "widgets"), "widgets"),
    (str(PROJECT_ROOT / "installable_widgets"), "installable_widgets"),
    (
        str(PROJECT_ROOT / "src" / "proxdeck" / "presentation" / "assets"),
        "proxdeck/presentation/assets",
    ),
]

hiddenimports = collect_submodules("proxdeck")


a = Analysis(
    ["main.py"],
    pathex=[str(PROJECT_ROOT), str(PROJECT_ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ProxDeck",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ProxDeck",
)
