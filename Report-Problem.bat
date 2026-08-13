@echo off
title VoiceMask - Report a problem
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
echo Collecting information...
uv run voicemask doctor > "%USERPROFILE%\Desktop\voicemask-report.txt" 2>&1
type "%LOCALAPPDATA%\VoiceMask\voicemask.log" >> "%USERPROFILE%\Desktop\voicemask-report.txt" 2>nul
echo.
echo Saved to your Desktop as voicemask-report.txt
pause
