@echo off
set PYTHONPATH=%cd%\aerosar_dashboard
.\.venv\Scripts\python.exe -m pytest aerosar_dashboard\tests
