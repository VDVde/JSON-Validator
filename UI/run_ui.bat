@echo off
REM VDV463 Validator UI Launcher for Windows
REM Requires: PySide6 (pip install PySide6)

echo Clearing Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc
echo.

echo Starting VDV463 JSON Validator UI...
echo Framework: PySide6
echo.

python main_ui.py

if errorlevel 1 (
    echo.
    echo Error: Failed to start the application.
    echo Please ensure:
    echo   - Python 3.10+ is installed
    echo   - PySide6 is installed (pip install PySide6)
    echo   - All dependencies are available
    pause
)
