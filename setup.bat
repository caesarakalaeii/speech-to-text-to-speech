@echo off
REM Windows Setup Launcher for speech-to-text-to-speech
REM This script launches the PowerShell installer with Administrator privileges

echo.
echo ========================================================================
echo   Speech-to-Text-to-Speech - Windows Setup
echo ========================================================================
echo.
echo This installer will automatically set up:
echo   - Python 3.11
echo   - FFmpeg (audio/video processing)
echo   - espeak-ng (text-to-speech phonetics)
echo   - CUDA Toolkit (optional, for GPU acceleration)
echo   - Python dependencies
echo.
echo NOTE: This script requires Administrator privileges to install
echo       system dependencies. You will be prompted for elevation.
echo.
echo ========================================================================
echo.

REM Check if PowerShell is available
powershell -Command "Write-Host 'PowerShell detected'" >nul 2>&1
if errorlevel 1 (
    echo Error: PowerShell is not available on this system.
    echo Please install PowerShell or run install.bat instead.
    pause
    exit /b 1
)

REM Launch PowerShell script with elevation
echo Launching installer...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "& {Start-Process PowerShell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"%~dp0setup-windows.ps1\"' -Verb RunAs -Wait}"

if errorlevel 1 (
    echo.
    echo Installation failed or was cancelled.
    pause
    exit /b 1
)

echo.
echo Setup complete!
pause
