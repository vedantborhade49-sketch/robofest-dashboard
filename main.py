import sys
import os
import subprocess

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aerosar_dashboard")
VENV_PYTHON = os.path.join(BASE_DIR, "venv", "Scripts", "python.exe")

# If PySide6 is not found in the current Python environment, auto-delegate to project venv
try:
    import PySide6
except ImportError:
    if os.path.exists(VENV_PYTHON) and sys.executable.lower() != VENV_PYTHON.lower():
        sys.exit(subprocess.call([VENV_PYTHON] + sys.argv))

sys.path.insert(0, BASE_DIR)

from aerosar_dashboard.main import main

if __name__ == "__main__":
    main()
