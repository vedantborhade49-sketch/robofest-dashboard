# STALLION AEROSAR — Ground Station Dashboard

This is the Ground Station Dashboard for the STALLION AEROSAR project (autonomous search-and-rescue drone operating in GPS-denied/confined environments).

## Current Development Stage
**Phase 1**: Initial project architecture, environment setup, and application skeleton. The UI currently displays a simple empty dark-themed window, establishing the foundation for future modules.

## Technology Stack
- **Python 3.11+**
- **PySide6** (Qt6 for UI)
- **Pydantic** (Data modeling)
- **PyQtGraph** (Fast graphing, to be used for telemetry/visualizations)

## Architecture Overview
The application follows a clean modular architecture ensuring the UI does not directly depend on the data source.
`UI -> Data Service -> Data Provider (Mock/Live)`

## Installation & Setup

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

```bash
python main.py
```
