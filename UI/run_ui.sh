#!/bin/bash
# VDV463 Validator UI Launcher for Linux/macOS
# Requires: PySide6 (pip install PySide6)

echo "Clearing Python cache..."
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
echo ""

echo "Starting VDV463 JSON Validator UI..."
echo "Framework: PySide6"
echo ""

python3 main_ui.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Error: Failed to start the application."
    echo "Please ensure:"
    echo "  - Python 3.10+ is installed"
    echo "  - PySide6 is installed (pip install PySide6)"
    echo "  - All dependencies are available"
    read -p "Press Enter to continue..."
fi
