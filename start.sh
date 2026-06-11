#!/bin/bash

echo "=================================================="
echo "  MDM Hierarchy Navigator - Startup Script"
echo "=================================================="
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo

# Check if Flask is installed
if python3 -c "import flask" 2>/dev/null; then
    echo "✓ Flask is already installed"
else
    echo "⚠️  Flask not found. Installing dependencies..."
    pip3 install Flask flask-cors requests
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        echo "Please run manually: pip3 install Flask flask-cors requests"
        exit 1
    fi
    echo "✓ Dependencies installed"
fi

echo
echo "=================================================="
echo "  Starting Flask server on http://localhost:8080"
echo "=================================================="
echo
echo "Press Ctrl+C to stop the server"
echo

# Start the Flask app
python3 app.py
