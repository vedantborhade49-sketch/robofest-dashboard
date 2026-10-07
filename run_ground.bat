@echo off
cd /d "%~dp0"

echo [Launcher] Starting GROUND_STATION Mode...
if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.\.venv\Scripts\python.exe
) else if exist "venv\Scripts\python.exe" (
    set PYTHON_EXE=.\venv\Scripts\python.exe
) else (
    echo "Virtual environment not found!"
    pause
    exit /b
)
set PYTHONPATH=%~dp0aerosar_dashboard
%PYTHON_EXE% -m app.integration.launcher --mode GROUND_STATION
pause
