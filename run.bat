@echo off
echo Starting Speech-to-Text application...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Error: Virtual environment not found.
    echo Please run setup.bat first to set up the environment.
    pause
    exit /b 1
)

REM Check if .env exists
if not exist ".env" (
    echo Warning: .env file not found.
    echo Copying .env.example to .env...
    copy .env.example .env
    echo Please edit .env to configure your settings before running again.
    pause
    exit /b 1
)

REM Activate virtual environment and run
call venv\Scripts\activate.bat
python main.py

REM Keep window open if there's an error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with an error.
    pause
)
