#!/bin/bash

echo "================================================"
echo "Park Up Edge Node - Automatic Setup for Linux/macOS"
echo "================================================"
echo

echo "[1/6] Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

python3 --version

echo
echo "[2/6] Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi

echo
echo "[3/6] Activating virtual environment..."
source venv/bin/activate

echo
echo "[4/6] Upgrading pip..."
python -m pip install --upgrade pip

echo
echo "[5/6] Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    echo "Try installing manually: pip install -r requirements.txt"
    exit 1
fi

echo
echo "[6/6] Setting up environment file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Environment file created: .env"
    echo "Please edit .env with your MySQL and ESP32 configurations"
else
    echo "Environment file already exists: .env"
fi

echo
echo "================================================"
echo "Setup completed successfully!"
echo "================================================"
echo
echo "Next steps:"
echo "1. Edit .env file with your configurations"
echo "2. Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo "3. Test ESP32 camera: python improved_plate_reader.py"
echo
echo "To activate virtual environment later:"
echo "source venv/bin/activate"
