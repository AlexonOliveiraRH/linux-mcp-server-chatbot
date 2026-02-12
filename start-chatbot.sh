#!/bin/bash
# Quick start script for Linux MCP Server Chatbot

set -e

echo "🐧 Linux MCP Server Chatbot Launcher"
echo "===================================="
echo

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "   Copy .env.example to .env and configure it:"
    echo "   cp .env.example .env"
    echo "   nano .env"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d .venv ]; then
    echo "❌ Virtual environment not found!"
    echo "   Create it with:"
    echo "   python -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source .venv/bin/activate

# Run setup verification
echo "✓ Verifying setup..."
echo
if python tests/test_setup.py; then
    echo
    echo "✓ All checks passed!"
    echo
else
    echo
    echo "⚠️  Some checks failed. See errors above."
    echo
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start Streamlit
echo "🚀 Starting chatbot..."
echo
echo "   The chatbot will open in your browser at:"
echo "   http://localhost:8501"
echo
echo "   Press Ctrl+C to stop"
echo

streamlit run app.py
