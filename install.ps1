#
# Claude Session Keeper - Windows Installer (PowerShell)
# Usage: irm https://raw.githubusercontent.com/nomadictuba2005/claude-session-keeper/main/install.ps1 | iex
#
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        Claude Session Keeper - Windows Installer          ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Installation paths
$InstallDir = "$env:USERPROFILE\.claude-session-keeper"
$BinDir = "$env:USERPROFILE\.local\bin"

# Create directories
Write-Host "Creating installation directory..." -ForegroundColor Blue
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

# Check for Python
Write-Host "Checking Python installation..." -ForegroundColor Blue
$PythonCmd = $null

try {
    $PythonVersion = & python --version 2>&1
    if ($PythonVersion -match "Python 3") {
        $PythonCmd = "python"
        Write-Host "Found $PythonVersion" -ForegroundColor Green
    }
} catch {}

if (-not $PythonCmd) {
    try {
        $PythonVersion = & python3 --version 2>&1
        if ($PythonVersion -match "Python 3") {
            $PythonCmd = "python3"
            Write-Host "Found $PythonVersion" -ForegroundColor Green
        }
    } catch {}
}

if (-not $PythonCmd) {
    Write-Host "Error: Python 3 is required but not installed." -ForegroundColor Red
    Write-Host "Please install Python 3.7+ from https://python.org and try again."
    exit 1
}

# Download files
Write-Host "Downloading Claude Session Keeper..." -ForegroundColor Blue
$RepoUrl = "https://raw.githubusercontent.com/nomadictuba2005/claude-session-keeper/main"

$Files = @(
    "claude_health_check_cli.py",
    "session_stats.py",
    "notifications.py",
    "profiles.py",
    "interactive_cli.py",
    "web_dashboard.py",
    "requirements.txt"
)

foreach ($File in $Files) {
    Write-Host "  Downloading $File..."
    Invoke-WebRequest -Uri "$RepoUrl/$File" -OutFile "$InstallDir\$File" -UseBasicParsing
}

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Blue
& $PythonCmd -m pip install --user -q requests pytz flask 2>$null

# Create batch wrapper
Write-Host "Creating CLI commands..." -ForegroundColor Blue

$BatchContent = @"
@echo off
cd /d "$InstallDir"
python claude_health_check_cli.py %*
"@

Set-Content -Path "$BinDir\claude-session-keeper.bat" -Value $BatchContent
Set-Content -Path "$BinDir\csk.bat" -Value $BatchContent

# Create PowerShell wrapper
$PSContent = @"
`$env:PYTHONPATH = "$InstallDir"
Set-Location "$InstallDir"
& python claude_health_check_cli.py `$args
"@

Set-Content -Path "$BinDir\claude-session-keeper.ps1" -Value $PSContent
Set-Content -Path "$BinDir\csk.ps1" -Value $PSContent

# Add to PATH
$UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($UserPath -notlike "*$BinDir*") {
    Write-Host "Adding to PATH..." -ForegroundColor Yellow
    [Environment]::SetEnvironmentVariable("PATH", "$BinDir;$UserPath", "User")
    $env:PATH = "$BinDir;$env:PATH"
}

# Create default config
if (-not (Test-Path "$InstallDir\config.json")) {
    '{"webhook_url": ""}' | Set-Content -Path "$InstallDir\config.json"
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║        Installation Complete!                             ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Installed to: $InstallDir" -ForegroundColor Blue
Write-Host ""
Write-Host "Commands:" -ForegroundColor Blue
Write-Host "  claude-session-keeper    - Full command"
Write-Host "  csk                      - Short alias"
Write-Host ""
Write-Host "Quick Start:" -ForegroundColor Yellow
Write-Host "  csk --help               - Show all options"
Write-Host "  csk --interactive        - Launch interactive menu"
Write-Host "  csk --web                - Start web dashboard"
Write-Host "  csk --once               - Run single health check"
Write-Host ""
Write-Host "Note: Restart your terminal to use the commands." -ForegroundColor Yellow
Write-Host ""
Write-Host "Enjoy using Claude Session Keeper!" -ForegroundColor Green
