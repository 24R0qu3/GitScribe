# install.ps1 — download and install gitscribe from the latest GitHub release.
#
# Usage (PowerShell):
#   irm https://raw.githubusercontent.com/24R0qu3/GitScribe/main/install.ps1 | iex
#
# Uninstall (semi — removes from Claude Code only):
#   $env:GITSCRIBE_UNINSTALL = "1"; irm https://raw.githubusercontent.com/24R0qu3/GitScribe/main/install.ps1 | iex
#
# Uninstall (full — also removes binary):
#   $env:GITSCRIBE_UNINSTALL = "full"; irm https://raw.githubusercontent.com/24R0qu3/GitScribe/main/install.ps1 | iex
param(
    [string]$InstallDir = $env:INSTALL_DIR,
    [string]$Uninstall  = $env:GITSCRIBE_UNINSTALL
)

$ErrorActionPreference = "Stop"

$Repo    = "24R0qu3/GitScribe"
$BinName = "gitscribe"

if (-not $InstallDir) {
    $InstallDir = Join-Path $env:LOCALAPPDATA "Programs\$BinName"
}

$Dest = Join-Path $InstallDir "$BinName.exe"

# ── Uninstall ─────────────────────────────────────────────────────────────────
if ($Uninstall) {
    if (Test-Path $Dest) {
        & $Dest patch-claude --remove
        if ($Uninstall -eq "full") {
            Remove-Item $Dest -Force
            Write-Host "Removed $Dest"
        }
    } else {
        Write-Host "gitscribe not found at $Dest — nothing to uninstall."
    }
    Write-Host "Done."
    exit 0
}

# ── Resolve latest release tag ────────────────────────────────────────────────
Write-Host "Fetching latest release..."
$Release = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/latest"
$Tag     = $Release.tag_name

# ── Download binary ───────────────────────────────────────────────────────────
$Url = "https://github.com/$Repo/releases/download/$Tag/${BinName}-${Tag}-windows.exe"
Write-Host "Downloading $BinName $Tag..."

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Invoke-WebRequest -Uri $Url -OutFile $Dest
Write-Host "Installed to $Dest"

# ── Add to user PATH ──────────────────────────────────────────────────────────
$UserPath = [Environment]::GetEnvironmentVariable("PATH", "User") ?? ""
if ($UserPath -notlike "*$InstallDir*") {
    $NewPath = ($UserPath.TrimEnd(";") + ";$InstallDir").TrimStart(";")
    [Environment]::SetEnvironmentVariable("PATH", $NewPath, "User")
    Write-Host "Added $InstallDir to user PATH (restart terminal to take effect)"
}

# ── Register with Claude Code ─────────────────────────────────────────────────
& $Dest patch-claude
Write-Host "Done. Restart Claude Code to activate gitscribe."
