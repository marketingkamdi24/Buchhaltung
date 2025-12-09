#!/bin/bash
# Start script for Buchhaltung on Unix/Linux/Mac
# Run this script with: chmod +x start.sh && ./start.sh

echo "==============================================="
echo "  Buchhaltung - Starting Application"
echo "==============================================="
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment not found."
    echo "Please run setup.sh first."
    exit 1
fi

echo "[INFO] Activating virtual environment..."
source venv/bin/activate

echo "[INFO] Starting Buchhaltung..."
echo
python run.py