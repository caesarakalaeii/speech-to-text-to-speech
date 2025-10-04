#!/bin/bash
set -e

echo "Starting Speech-to-Text application..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found."
    echo "Please run ./setup.sh first to set up the environment."
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found."
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo "Please edit .env to configure your settings before running again."
    exit 1
fi

# Activate virtual environment and run
source venv/bin/activate
python main.py
