@echo off
REM Setup script for Buchhaltung on Windows
REM Run this script with: setup.bat

echo ===============================================
echo   Buchhaltung - Setup Script for Windows
echo ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

echo [INFO] Python found:
python --version

echo.
echo [INFO] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo [OK] Virtual environment created.
) else (
    echo [OK] Virtual environment already exists.
)

echo.
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [INFO] Installing dependencies...
pip install -r requirements.txt

echo.
echo [INFO] Creating output directory...
if not exist "output" mkdir output

echo.
echo ===============================================
echo   Setup Complete!
echo ===============================================
echo.
echo To run the application:
echo   1. Activate the virtual environment: venv\Scripts\activate.bat
echo   2. Run the application: python run.py
echo.
echo Or simply run: start.bat
echo.
pause