@echo off
cd /d "%~dp0"

echo [Launcher] Starting LAPTOP Mode...
if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.\.venv\Scripts\python.exe
) else if exist "venv\Scripts\python.exe" (
    set PYTHON_EXE=.\venv\Scripts\python.exe
) else (
    echo "Virtual environment not found!"
    pause
    exit /b
)

%PYTHON_EXE% -m aerosar_dashboard.app.integration.launcher --mode LAPTOP
pause
