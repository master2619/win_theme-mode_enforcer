@echo off
echo Windows Theme Monitor - Installation Script
echo ==========================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

echo Installing required packages...
pip install -r "C:\Users\deepe\Downloads\exported-assets\WindowsThemeMonitor_Complete\ThemeMonitor\requirements.txt"

if %errorlevel% neq 0 (
    echo Error: Failed to install requirements
    pause
    exit /b 1
)

echo.
echo Installation complete!
echo You can now run the application with: python main.py
echo.
echo To build as executable, run: pyinstaller --onefile --noconsole --icon=assets/icon.ico main.py
echo.
pause
