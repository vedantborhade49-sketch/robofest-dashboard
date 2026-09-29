import sys
import traceback
from PySide6.QtCore import QCoreApplication

try:
    app = QCoreApplication(sys.argv)
    from app.services.data_service import DataService
    ds = DataService()
    print("SUCCESS")
except Exception as e:
    print("CRASHED")
    traceback.print_exc()
