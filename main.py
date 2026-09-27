import sys
import os

# Add aerosar_dashboard to sys.path
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aerosar_dashboard")
sys.path.insert(0, BASE_DIR)

from aerosar_dashboard.main import main

if __name__ == "__main__":
    main()
