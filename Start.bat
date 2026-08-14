@echo off
title Speech-to-Text-to-Speech
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
start "" ".venv\Scripts\pythonw.exe" -m stts.cli
