@echo off
REM run_textual_4p_round.bat - Launches compact round-table TUI
set "PROJECT_DIR=%~dp0"
if exist "%PROJECT_DIR%\.venv\Scripts\activate.bat" (
  call "%PROJECT_DIR%\.venv\Scripts\activate.bat"
)
python -m ui.tiqqun_textual_4p_round
pause
