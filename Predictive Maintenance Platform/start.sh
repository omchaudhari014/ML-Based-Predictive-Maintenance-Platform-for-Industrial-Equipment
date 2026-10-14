#!/bin/bash
set -e
echo "============================================================"
echo "  ML-Based Predictive Maintenance Platform"
echo "============================================================"
echo

cd "$(dirname "$0")/backend"

if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt -q

if [ ! -f ml_artifacts/selected_model.joblib ]; then
    echo
    echo "Training ML models (first run)..."
    python prepare_ml.py
fi

echo
echo "Starting server..."
echo "Open http://localhost:5000 in your browser"
echo
python server.py
