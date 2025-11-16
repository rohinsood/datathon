#!/bin/bash
# Quick start script for ML API server

echo "🚀 Starting ML API Server..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Run the server
echo ""
echo "="*70
echo "✅ Starting Flask API on http://localhost:5000"
echo "="*70
echo ""

python app.py

