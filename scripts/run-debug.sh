#!/bin/bash
# Run chatbot with debug output

set -e

echo "🔍 Starting chatbot in debug mode..."
echo

# Activate virtual environment
source .venv/bin/activate

# Clear Streamlit cache
rm -rf .streamlit 2>/dev/null
echo "✓ Cache cleared"
echo

# Set debug environment
export STREAMLIT_LOG_LEVEL=debug

# Run Streamlit
echo "Starting Streamlit..."
echo "Watch for [DEBUG] messages in the output below"
echo
streamlit run app.py 2>&1 | tee streamlit.log
