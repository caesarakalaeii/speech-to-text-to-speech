@echo off
title Speech-to-Text-to-Speech - Install
cd /d "%~dp0"
echo.
echo   Installing Speech-to-Text-to-Speech. This takes about 10 minutes and needs internet.
echo   You do not need Python - it will be set up for you.
echo.

set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>&1
if errorlevel 1 (
    echo   [1/3] Getting the setup tool...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if errorlevel 1 goto fail
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)

echo   [2/3] Installing Speech-to-Text-to-Speech...
uv sync --no-dev
if errorlevel 1 goto fail

echo   [3/3] Downloading voices and models...
uv run python -m stts.install
if errorlevel 1 goto fail

echo.
echo   Done. Open Speech-to-Text-to-Speech from the desktop shortcut.
pause
exit /b 0

:fail
echo.
echo   Install failed. Check your internet connection and try again.
echo   If it keeps failing, run Report-Problem.bat and send the file it makes.
pause
exit /b 1
