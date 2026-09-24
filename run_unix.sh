#!/usr/bin/env bash
# Unix/macOS Launch Script for NexStock Enterprise Suite
echo "Starting NexStock Enterprise Platform..."

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

echo "Starting FastAPI Backend on port 8001..."
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload &
BACKEND_PID=$!

sleep 3

echo "Starting Streamlit Executive Dashboard on port 8501..."
streamlit run frontend/app.py --server.port 8501

# Cleanup backend on exit
kill $BACKEND_PID
