@echo off
REM Simple Installation Script for speech-to-text-to-speech
REM This script runs the Python-based installer (no admin required)
REM For automatic system dependency installation, use setup.bat instead

echo.
echo ========================================================================
echo   Speech-to-Text-to-Speech Installer (Windows)
echo ========================================================================
echo.
echo This script will:
echo   - Create a Python virtual environment
echo   - Install Python dependencies
echo   - Set up configuration files
echo.
echo NOTE: This script assumes you already have:
echo   - Python 3.8+ installed and in PATH
echo   - FFmpeg installed (for audio processing)
echo   - espeak-ng installed (for NeuTTS only)
echo.
echo If you need automatic installation of system dependencies,
echo please use setup.bat instead (requires Administrator).
echo.
echo ========================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo.
    echo Please either:
    echo   1. Run setup.bat for automatic installation (requires Admin)
    echo   2. Manually install Python 3.8+ from https://www.python.org/downloads/
    echo      Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Run the Python installer
python install.py

if errorlevel 1 (
    echo.
    echo Installation failed or was cancelled
    pause
    exit /b 1
)

echo.
echo Installation script completed
pause
