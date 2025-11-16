#!/bin/bash

echo "Starting College Affordability ML API..."
echo "========================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing/updating dependencies..."
pip install -r requirements.txt

# Start the Flask API
echo "========================================"
echo "Starting Flask server on http://localhost:5000"
echo "Press Ctrl+C to stop"
echo "========================================"
python app.py

