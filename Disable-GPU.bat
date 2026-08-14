@echo off
title Speech-to-Text-to-Speech - Back to processor
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
uv pip uninstall onnxruntime-directml
uv sync --no-dev
echo Done - Speech-to-Text-to-Speech will use the processor again.
pause
