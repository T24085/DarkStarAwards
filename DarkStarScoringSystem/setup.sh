#!/bin/bash
# Setup script for DSSS on Jetson Nano

echo "Setting up Dark Star Scoring System..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

# Install Lighthouse (requires Node.js)
if command -v npm &> /dev/null; then
    echo "Installing Lighthouse..."
    npm install -g lighthouse
else
    echo "Warning: npm not found. Install Node.js to use Lighthouse."
fi

# Create directories
echo "Creating directories..."
mkdir -p artifacts
mkdir -p credentials

# Check Ollama
if command -v ollama &> /dev/null; then
    echo "Ollama found. Pulling model..."
    ollama pull llama3.1:8b
else
    echo "Warning: Ollama not found. Install Ollama to use AI scoring."
fi

echo "Setup complete!"
echo "Next steps:"
echo "1. Copy .env.example to .env and configure"
echo "2. Place Firebase credentials in credentials/firebase-service-account.json"
echo "3. Run: python3 -m judge_worker.main"

