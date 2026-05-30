@echo off
REM One-time setup: creates a virtual environment and installs all dependencies.
REM Run this once after cloning or unzipping the project, then use: python main.py

echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: 'python' not found. Install Python 3.11 or 3.12 from https://python.org
    pause
    exit /b 1
)

echo Installing dependencies...
venv\Scripts\pip install --upgrade pip -q
venv\Scripts\pip install -r requirements.txt -q

echo.
echo Setup complete!
echo Run the app with:  python main.py
pause
