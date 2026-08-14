@echo off
title Speech-to-Text-to-Speech - Try GPU acceleration
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
echo Measuring speed on the processor first...
uv run stts bench
echo.
echo Installing GPU support (DirectML)...
uv pip install onnxruntime-directml
if errorlevel 1 goto fail
echo.
echo Measuring speed on the graphics card...
uv run stts bench --gpu
echo.
echo Compare the two totals above. If the GPU is NOT faster, run Disable-GPU.bat.
pause
exit /b 0
:fail
echo Could not install GPU support. Nothing was changed.
pause
exit /b 1
