@echo off
set "PROJECT_DIR=%~dp0"
if exist "%PROJECT_DIR%\.venv\Scripts\activate.bat" (
  call "%PROJECT_DIR%\.venv\Scripts\activate.bat"
)
python -m ui.tiqqun_tk_clock
pause
