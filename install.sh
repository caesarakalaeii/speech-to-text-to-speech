#!/bin/bash
# Linux/macOS Installation Script for speech-to-text-to-speech
# This script runs the Python installer

echo ""
echo "========================================================================"
echo "  Speech-to-Text-to-Speech Installer (Linux/macOS)"
echo "========================================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8+ using your package manager"
    exit 1
fi

# Run the Python installer
python3 install.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Installation failed or was cancelled"
    exit 1
fi

echo ""
echo "Installation script completed"
