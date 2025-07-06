@echo off
echo ================================================
echo Park Up Edge Node - Automatic Setup for Windows
echo ================================================
echo.

echo [1/6] Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher
    pause
    exit /b 1
)

echo.
echo [2/6] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo.
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [4/6] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [5/6] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    echo Try installing manually: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo [6/6] Setting up environment file...
if not exist .env (
    copy .env.example .env
    echo Environment file created: .env
    echo Please edit .env with your MySQL and ESP32 configurations
) else (
    echo Environment file already exists: .env
)

echo.
echo ================================================
echo Setup completed successfully!
echo ================================================
echo.
echo Next steps:
echo 1. Edit .env file with your configurations
echo 2. Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000
echo 3. Test ESP32 camera: python improved_plate_reader.py
echo.
echo Press any key to exit...
pause >nul
