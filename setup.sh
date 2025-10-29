#!/bin/bash
# Quick setup script for Linux/Mac

echo "🎤 Karaoke Automation System - Quick Setup"
echo "=========================================="

# Check Python version
echo ""
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required_version="3.9"

if (( $(echo "$python_version < $required_version" | bc -l) )); then
    echo "❌ Python 3.9+ required. You have: $python_version"
    exit 1
else
    echo "✅ Python $python_version detected"
fi

# Check FFmpeg
echo ""
echo "Checking FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg not found. Please install FFmpeg first:"
    echo "   Ubuntu/Debian: sudo apt install ffmpeg"
    echo "   macOS: brew install ffmpeg"
    exit 1
else
    echo "✅ FFmpeg found"
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate
echo "✅ Virtual environment created"

# Install dependencies
echo ""
echo "Installing dependencies (this may take a while)..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Create .env file
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your YouTube API key"
fi

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your YouTube API key"
echo "2. (Optional) Download client_secrets.json for YouTube upload"
echo "3. Run: python main.py"
echo ""
echo "Happy karaoke-ing! 🎤"
