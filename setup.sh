#!/bin/bash
set -e

echo "================================================"
echo "Speech-to-Text-to-Speech Setup Script"
echo "================================================"
echo ""

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Found Python $PYTHON_VERSION"

# Check for pip
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed. Please install pip3."
    exit 1
fi

# Check for PortAudio (required for PyAudio)
echo ""
echo "Checking for PortAudio (required for microphone input)..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if ! dpkg -l | grep -q portaudio19-dev; then
        echo "Installing PortAudio..."
        sudo apt-get update
        sudo apt-get install -y portaudio19-dev
    else
        echo "PortAudio is already installed"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    if ! brew list portaudio &> /dev/null; then
        echo "Installing PortAudio..."
        brew install portaudio
    else
        echo "PortAudio is already installed"
    fi
else
    echo "Warning: Please ensure PortAudio is installed on your system"
fi

# Check for ffmpeg (required for Whisper)
echo ""
echo "Checking for ffmpeg (required for Whisper)..."
if ! command -v ffmpeg &> /dev/null; then
    echo "Installing ffmpeg..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get install -y ffmpeg
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ffmpeg
    else
        echo "Error: Please install ffmpeg manually"
        exit 1
    fi
else
    echo "ffmpeg is already installed"
fi

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env to configure your Speakerbot WebSocket URL"
fi

echo ""
echo "================================================"
echo "Setup completed successfully!"
echo "================================================"
echo ""
echo "To run the application:"
echo "  1. Edit .env to configure your settings"
echo "  2. Activate the virtual environment: source venv/bin/activate"
echo "  3. Run the application: python main.py"
echo ""
echo "To deactivate the virtual environment later: deactivate"
echo ""
