import os
import sys

# Add aerosar_dashboard to sys.path so that 'from app.*' imports work correctly
dashboard_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aerosar_dashboard")
sys.path.insert(0, dashboard_dir)

from app.integration.launcher import run_simulation

if __name__ == "__main__":
    print("==================================================")
    print(" AEROSAR Step 29: Complete E2E Integration Simulation ")
    print("==================================================")
    run_simulation()
