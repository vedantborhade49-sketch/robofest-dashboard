@echo off
cd /d "%~dp0"

echo [Simulator] Checking for existing processes on port 8000...
for /f "tokens=5" %%a in ('netstat -a -n -o ^| findstr :8000') do (
    if %%a neq 0 (
        echo [Simulator] Killing lingering process with PID %%a...
        taskkill /F /PID %%a >nul 2>&1
        timeout /t 2 /nobreak >nul
    )
)

if exist ".venv\Scripts\python.exe" (
    .\.venv\Scripts\python.exe run_simulation.py
) else if exist "venv\Scripts\python.exe" (
    .\venv\Scripts\python.exe run_simulation.py
) else (
    echo "Virtual environment not found! Please create a .venv folder and install requirements."
)
pause
