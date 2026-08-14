@echo off
title Speech-to-Text-to-Speech - Report a problem
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
echo Collecting information...
uv run stts doctor > "%USERPROFILE%\Desktop\stts-report.txt" 2>&1
type "%LOCALAPPDATA%\stts\stts.log" >> "%USERPROFILE%\Desktop\stts-report.txt" 2>nul
echo.
echo Saved to your Desktop as stts-report.txt
pause
