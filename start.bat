@echo off
REM Start script for Buchhaltung on Windows
REM Run this script with: start.bat

echo ===============================================
echo   Buchhaltung - Starting Application
echo ===============================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [ERROR] Virtual environment not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Starting Buchhaltung...
echo.
python run.py

pause