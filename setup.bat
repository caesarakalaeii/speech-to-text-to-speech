@echo off
echo ================================================
echo Speech-to-Text-to-Speech Setup Script (Windows)
echo ================================================
echo.

REM Check for Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%

REM Check for pip
python -m pip --version >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: pip is not installed. Please install pip.
    exit /b 1
)

REM Check for ffmpeg
echo.
echo Checking for ffmpeg (required for Whisper)...
where ffmpeg >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: ffmpeg is not installed or not in PATH.
    echo.
    echo Please install ffmpeg:
    echo 1. Download from https://www.gyan.dev/ffmpeg/builds/
    echo 2. Extract the archive
    echo 3. Add the bin folder to your PATH environment variable
    echo.
    echo OR use Chocolatey: choco install ffmpeg
    echo OR use Scoop: scoop install ffmpeg
    echo.
    echo Press any key to continue anyway or Ctrl+C to exit...
    pause >nul
) else (
    echo ffmpeg is already installed
)

REM Create virtual environment
echo.
echo Creating Python virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install Python dependencies
echo.
echo Installing Python dependencies...
echo Note: PyAudio installation on Windows may require Microsoft C++ Build Tools
echo If installation fails, you can install a pre-built wheel from:
echo https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
echo.
pip install -r requirements.txt

REM Copy environment file if it doesn't exist
if not exist ".env" (
    echo.
    echo Creating .env file from template...
    copy .env.example .env
    echo Please edit .env to configure your Speakerbot WebSocket URL
)

echo.
echo ================================================
echo Setup completed successfully!
echo ================================================
echo.
echo To run the application:
echo   1. Edit .env to configure your settings
echo   2. Run: run.bat
echo.
echo Note: If you encounter PyAudio issues, you may need to:
echo - Install Microsoft C++ Build Tools
echo - Or download a pre-built PyAudio wheel from:
echo   https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
echo   Then install with: pip install PyAudio-X.X.X-cpXX-cpXX-win_amd64.whl
echo.
pause
