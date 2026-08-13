@echo off
title VoiceMask
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
start "" ".venv\Scripts\pythonw.exe" -m voicemask.cli
