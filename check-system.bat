@echo off
REM System Check Script for speech-to-text-to-speech
REM Checks what's installed and recommends installation method

echo.
echo ========================================================================
echo   Speech-to-Text-to-Speech - System Check
echo ========================================================================
echo.
echo This script will check your system for required dependencies.
echo.
echo ========================================================================
echo.

set PYTHON_OK=0
set FFMPEG_OK=0
set ESPEAK_OK=0
set CUDA_OK=0
set ISSUES=0

REM Check Python
echo [1/4] Checking for Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   X Python NOT FOUND
    set /a ISSUES+=1
) else (
    echo   + Python found:
    python --version 2>&1 | findstr /C:"Python"
    
    REM Check version
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
    echo   Version: %PYTHON_VERSION%
    set PYTHON_OK=1
)
echo.

REM Check FFmpeg
echo [2/4] Checking for FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo   X FFmpeg NOT FOUND
    set /a ISSUES+=1
) else (
    echo   + FFmpeg found:
    ffmpeg -version 2>&1 | findstr /C:"ffmpeg version"
    set FFMPEG_OK=1
)
echo.

REM Check espeak-ng
echo [3/4] Checking for espeak-ng (required for NeuTTS)...
espeak-ng --version >nul 2>&1
if errorlevel 1 (
    echo   X espeak-ng NOT FOUND
    echo   Note: Only needed if you want to use NeuTTS Air
    set /a ISSUES+=1
) else (
    echo   + espeak-ng found:
    espeak-ng --version 2>&1 | findstr /C:"eSpeak NG"
    set ESPEAK_OK=1
)
echo.

REM Check CUDA
echo [4/4] Checking for CUDA Toolkit (optional, for GPU acceleration)...
nvcc --version >nul 2>&1
if errorlevel 1 (
    echo   - CUDA NOT FOUND (optional)
    echo   Note: Only needed for GPU acceleration
) else (
    echo   + CUDA found:
    nvcc --version 2>&1 | findstr /C:"release"
    set CUDA_OK=1
)
echo.

echo ========================================================================
echo   SUMMARY
echo ========================================================================
echo.

if %ISSUES%==0 (
    echo Status: ALL REQUIRED DEPENDENCIES FOUND!
    echo.
    echo You can proceed with installation using install.bat
    echo.
) else (
    echo Status: %ISSUES% ISSUE(S) FOUND
    echo.
    echo Missing dependencies:
    if %PYTHON_OK%==0 echo   - Python 3.8+
    if %FFMPEG_OK%==0 echo   - FFmpeg
    if %ESPEAK_OK%==0 echo   - espeak-ng (for NeuTTS only)
    echo.
)

echo ========================================================================
echo   RECOMMENDED INSTALLATION METHOD
echo ========================================================================
echo.

if %ISSUES%==0 (
    echo All dependencies found! You have two options:
    echo.
    echo Option 1: Quick Setup (RECOMMENDED)
    echo   - Run: install.bat
    echo   - Installs Python packages only
    echo   - No admin rights needed
    echo   - Fastest method
    echo.
    echo Option 2: Full Setup
    echo   - Run: setup.bat (as Administrator)
    echo   - Can reinstall/update all system dependencies
    echo   - Useful for updating or fixing installations
    echo.
) else (
    if %PYTHON_OK%==0 (
        echo CRITICAL: Python not found!
        echo.
        echo RECOMMENDATION: Run setup.bat as Administrator
        echo   - This will install ALL missing dependencies automatically
        echo   - Includes Python, FFmpeg, espeak-ng, and optionally CUDA
        echo   - Takes 20-30 minutes
        echo.
        echo Alternative: Install Python manually from python.org
        echo   - Make sure to check "Add Python to PATH"
        echo   - Then run this check again
        echo.
    ) else (
        if %FFMPEG_OK%==0 (
            echo Python found, but FFmpeg is missing.
            echo.
            echo RECOMMENDATION: Run setup.bat as Administrator
            echo   - Automatically installs FFmpeg and other dependencies
            echo.
            echo Alternative: Install FFmpeg manually:
            echo   - Using Chocolatey: choco install ffmpeg
            echo   - Using Scoop: scoop install ffmpeg
            echo   - Or download from: https://www.gyan.dev/ffmpeg/builds/
            echo.
        ) else (
            echo Python and FFmpeg found!
            echo.
            if %ESPEAK_OK%==0 (
                echo espeak-ng is missing (only needed for NeuTTS Air).
                echo.
                echo If you plan to use NeuTTS Air:
                echo   1. Run: setup.bat (as Administrator)
                echo   2. Or install manually from:
                echo      https://github.com/espeak-ng/espeak-ng/releases
                echo.
                echo If you only need Speakerbot TTS:
                echo   - You can proceed with: install.bat
                echo.
            )
        )
    )
)

echo ========================================================================
echo   QUICK ACTIONS
echo ========================================================================
echo.
echo [1] Run automated setup (installs missing dependencies)
echo     - Requires Administrator privileges
echo     - Right-click setup.bat and "Run as Administrator"
echo.
echo [2] Run Python package installer only
echo     - Requires Python and FFmpeg already installed
echo     - Double-click install.bat
echo.
echo [3] View detailed Windows setup guide
echo     - Open WINDOWS_SETUP.md in your browser
echo.
echo [4] View quick start guide
echo     - Open QUICKSTART.md in your browser
echo.
echo ========================================================================
echo.

if %ISSUES%==0 (
    choice /C YN /M "Do you want to run install.bat now (installs Python packages)"
    if errorlevel 2 goto :end
    if errorlevel 1 goto :run_install
) else (
    if %PYTHON_OK%==0 (
        echo Cannot run install.bat without Python.
        echo Please run setup.bat as Administrator first.
        echo.
        pause
        goto :end
    ) else (
        choice /C YN /M "Do you want to run install.bat now (some dependencies missing)"
        if errorlevel 2 goto :end
        if errorlevel 1 goto :run_install
    )
)

:run_install
echo.
echo Running install.bat...
echo.
call install.bat
goto :end

:end
echo.
echo System check complete.
pause
