#!/bin/bash

echo "Setting up Ollama for College Advisor..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "Ollama is already installed"
fi

# Start Ollama service
echo "Starting Ollama service..."
ollama serve &

# Wait a moment for service to start
sleep 3

# Pull the model
echo "Downloading llama3.2 model (this may take a few minutes)..."
ollama pull llama3.2

echo "Setup complete! Your college advisor is ready to use."
echo "You can now test queries like:"
echo "- 'Best value colleges in Texas'"
echo "- 'Most affordable colleges'"
echo "- 'Colleges with high graduation rates'"