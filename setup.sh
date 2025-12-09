#!/bin/bash
# Setup script for Buchhaltung on Unix/Linux/Mac
# Run this script with: chmod +x setup.sh && ./setup.sh

echo "==============================================="
echo "  Buchhaltung - Setup Script"
echo "==============================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed."
    echo "Please install Python 3.9+ from https://www.python.org/"
    exit 1
fi

echo "[INFO] Python found:"
python3 --version

echo
echo "[INFO] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "[OK] Virtual environment created."
else
    echo "[OK] Virtual environment already exists."
fi

echo
echo "[INFO] Activating virtual environment..."
source venv/bin/activate

echo
echo "[INFO] Upgrading pip..."
pip install --upgrade pip

echo
echo "[INFO] Installing dependencies..."
pip install -r requirements.txt

echo
echo "[INFO] Creating output directory..."
mkdir -p output

echo
echo "==============================================="
echo "  Setup Complete!"
echo "==============================================="
echo
echo "To run the application:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run the application: python run.py"
echo
echo "Or simply run: ./start.sh"
echo