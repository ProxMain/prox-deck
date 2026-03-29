# Prox Deck Release Flow

This repository now ships as `v1.0.0-alpha`.

## Prerequisites

- Windows
- Python 3.11+
- Inno Setup 6 if you want the `.exe` installer output

## Build

From the repository root:

```powershell
.\scripts\build-release.ps1
```

The script will:

1. install the release tooling into the selected Python environment
2. build a PyInstaller one-folder bundle at `dist\ProxDeck`
3. build an Inno Setup installer at `dist\installer` when `ISCC.exe` is installed

## Runtime Layout

- bundled widgets are shipped read-only with the installed application
- per-user state is written to `%LOCALAPPDATA%\ProxDeck`
- user-installed widgets are loaded from `%LOCALAPPDATA%\ProxDeck\installable_widgets`

This keeps the installer output immutable while preserving writable runtime state.
