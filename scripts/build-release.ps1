param(
    [string]$PythonExe = ".\.venv\Scripts\python.exe",
    [string]$Version = "1.0.0-alpha"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$distRoot = Join-Path $projectRoot "dist"
$installerOutput = Join-Path $distRoot "installer"
$specPath = Join-Path $projectRoot "proxdeck.spec"
$issPath = Join-Path $projectRoot "installer\proxdeck.iss"

if (-not (Test-Path $PythonExe)) {
    throw "Python executable not found at $PythonExe"
}

if (Test-Path $distRoot) {
    Remove-Item -LiteralPath $distRoot -Recurse -Force
}

New-Item -ItemType Directory -Path $installerOutput -Force | Out-Null

& $PythonExe -m pip install -e ".[release]"
& $PythonExe -m PyInstaller --noconfirm $specPath

function Resolve-IsccPath {
    $candidates = @()

    if ($env:ProgramFiles) {
        $candidates += (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
    }

    $programFilesX86 = [Environment]::GetEnvironmentVariable("ProgramFiles(x86)")
    if ($programFilesX86) {
        $candidates += (Join-Path $programFilesX86 "Inno Setup 6\ISCC.exe")
    }

    if ($env:LOCALAPPDATA) {
        $candidates += (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
    }

    foreach ($candidate in $candidates | Select-Object -Unique) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }

    $registryKeys = @(
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1"
    )

    foreach ($key in $registryKeys) {
        try {
            $installLocation = (Get-ItemProperty -Path $key -ErrorAction Stop).InstallLocation
            if ($installLocation) {
                $candidate = Join-Path $installLocation "ISCC.exe"
                if (Test-Path -LiteralPath $candidate) {
                    return $candidate
                }
            }
        } catch {
        }
    }

    return $null
}

$isccPath = Resolve-IsccPath

if (-not $isccPath) {
    Write-Warning "Inno Setup 6 was not found. The PyInstaller bundle is ready at dist\ProxDeck."
    exit 0
}

& $isccPath "/DMyAppVersion=$Version" "/O$installerOutput" $issPath
