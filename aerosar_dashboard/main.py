import sys
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(BASE_DIR, "venv", "Scripts", "python.exe")

# If PySide6 is not found in current environment, auto-delegate to venv
try:
    import PySide6
except ImportError:
    if os.path.exists(VENV_PYTHON) and sys.executable.lower() != VENV_PYTHON.lower():
        sys.exit(subprocess.call([VENV_PYTHON] + sys.argv))
    raise

# Ensure aerosar_dashboard directory is on sys.path
sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

