#!/bin/bash
# Telus AI Talent Intelligence Platform - One-Click Setup & Run Script
# This script works on macOS and Linux

echo "🚀 Telus AI Talent Intelligence Platform - One-Click Setup"
echo "=========================================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    echo "💡 Visit: https://python.org/downloads"
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Found Python $python_version"

# Run setup
echo ""
echo "🔧 Running setup..."
python3 setup.py

# Check if setup was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "🚀 Starting the application..."
    python3 run_project.py
else
    echo "❌ Setup failed. Please check the error messages above."
    exit 1
fi
