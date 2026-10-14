@echo off
echo ============================================================
echo   ML-Based Predictive Maintenance Platform
echo ============================================================
echo.

cd /d "%~dp0backend"

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt -q

if not exist ml_artifacts\selected_model.joblib (
    echo.
    echo Training ML models (first run)...
    python prepare_ml.py
)

echo.
echo Starting server...
echo Open http://localhost:5000 in your browser
echo.
python server.py
