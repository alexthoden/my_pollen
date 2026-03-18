@echo off
REM Pollen Tracker Setup Script for Windows

echo.
echo ==================================================
echo Pollen Tracker - Setup Script
echo ==================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://www.python.org/
    pause
    exit /b 1
)

echo [✓] Python found
echo.

REM Create virtual environment
echo Creating virtual environment...
if not exist venv (
    python -m venv venv
    echo [✓] Virtual environment created
) else (
    echo [✓] Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo [✓] Virtual environment activated
echo.

REM Install dependencies
echo Installing Python packages...
pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)
echo [✓] Dependencies installed
echo.

REM Check for .env file
if not exist .env (
    echo Creating .env file...
    (
        echo GOOGLE_POLLEN_API_KEY="YOUR_API_KEY_HERE"
    ) > .env
    echo [!] .env file created - PLEASE ADD YOUR GOOGLE POLLEN API KEY
    echo Get API key from: https://developers.google.com/maps/documentation/pollen/overview
) else (
    echo [✓] .env file exists
)
echo.

REM Create data directory
if not exist data (
    mkdir data
    echo [✓] Data directory created
) else (
    echo [✓] Data directory exists
)
echo.

REM Initialization complete
echo ==================================================
echo Setup complete!
echo ==================================================
echo.
echo Next steps:
echo 1. Edit .env and add your GOOGLE_POLLEN_API_KEY
echo 2. Run: python main.py
echo 3. Open http://localhost:5000 in your browser
echo.
echo To also launch the desktop GUI:
echo   python main.py --gui
echo.
pause
