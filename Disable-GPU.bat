@echo off
title VoiceMask - Back to processor
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
uv pip uninstall onnxruntime-directml
uv sync --no-dev
echo Done - VoiceMask will use the processor again.
pause
