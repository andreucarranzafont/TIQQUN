@echo off
REM run_textual_4p_v12.bat - launches the responsive 2x2 TUI
set "PROJECT_DIR=%~dp0"
if exist "%PROJECT_DIR%\.venv\Scripts\activate.bat" (
  call "%PROJECT_DIR%\.venv\Scripts\activate.bat"
)
python -m ui.tiqqun_textual_4p_v12
pause
