#!/bin/bash

# Pollen Tracker Setup Script for Linux/Mac

echo ""
echo "=================================================="
echo "Pollen Tracker - Setup Script"
echo "=================================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.7+ first"
    echo "Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "macOS: brew install python3"
    exit 1
fi

echo "[✓] Python found: $(python3 --version)"
echo ""

# Check if tkinter is available
echo "Checking tkinter (required for GUI)..."
python3 -m tkinter -c "print('Tkinter OK')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[!] Tkinter not found. Installing..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get install python3-tk
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "    macOS: Tkinter should be included with Python"
        echo "    If missing, reinstall Python from python.org"
    fi
fi
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "[✓] Virtual environment created"
else
    echo "[✓] Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "[✓] Virtual environment activated"
echo ""

# Install dependencies
echo "Installing Python packages..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi
echo "[✓] Dependencies installed"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
GOOGLE_POLLEN_API_KEY="YOUR_API_KEY_HERE"
EOF
    echo "[!] .env file created - PLEASE ADD YOUR GOOGLE POLLEN API KEY"
    echo "Get API key from: https://developers.google.com/maps/documentation/pollen/overview"
else
    echo "[✓] .env file exists"
fi
echo ""

# Create data directory
if [ ! -d "data" ]; then
    mkdir data
    echo "[✓] Data directory created"
else
    echo "[✓] Data directory exists"
fi
echo ""

# Make script executable
chmod +x run.sh 2>/dev/null

# Initialization complete
echo "=================================================="
echo "Setup complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your GOOGLE_POLLEN_API_KEY"
echo "2. Run: python3 main.py"
echo "3. Open http://localhost:5000 in your browser"
echo ""
echo "To also launch the desktop GUI:"
echo "   python3 main.py --gui"
echo ""
