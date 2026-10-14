# ML-Based Predictive Maintenance Platform

## Overview
A machine-learning predictive maintenance application that detects equipment failure risk from telemetry data. Uses traditional ML (scikit-learn + XGBoost) with TreeSHAP explanations, interactive 3D equipment visualization, and engineering-grade diagnostics.

Product story: Telemetry → Predict → Explain → Localize → Recommend → Simulate → Remember

## Features
- CSV upload with validation (max 1,000 records per analysis)
- Automated ML pipeline: Logistic Regression, Random Forest, Gradient Boosting, XGBoost
- Dynamic model selection by PR-AUC (currently selects: Gradient Boosting)
- Per-record Failure Risk Scoring (operational, not calibrated probability)
- TreeSHAP-based model explanations
- Engineering interpretation → physical inspection area mapping
- Interactive 3D conceptual equipment visualization (Three.js)
- Scenario simulation (what-if analysis)
- Analysis history (localStorage, optional Firebase/Firestore)

## Architecture
```
backend/
  server.py          — Flask REST API
  prepare_ml.py      — ML training pipeline
  ml_artifacts/      — Trained models, preprocessor, metrics
  data/              — AI4I 2020 dataset (training)
frontend/
  index.html         — Home page
  upload.html        — Dataset upload + validation
  analysis.html      — Pipeline progress
  results.html       — Results dashboard
  machine.html       — Diagnostics + 3D viewer
  model-performance.html — Model comparison
  history.html       — Analysis history
  js/                — Application JavaScript
  css/               — Design system
  assets/            — Static assets, Three.js, configs
```

## Prerequisites
- Python 3.10+ (3.13 tested)
- pip

## Installation & Running

### Quick Start (Windows)
```
start.bat
```

### Quick Start (Linux/Mac)
```
chmod +x start.sh
./start.sh
```

### Manual Setup
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux: source .venv/bin/activate
pip install -r requirements.txt

# Train ML models (required once)
python prepare_ml.py

# Start server
python server.py
```

Open http://localhost:5000 in your browser.

## ML Artifacts
The training pipeline (`prepare_ml.py`) produces:
- `preprocessor.joblib` — Fitted imputer + scaler (fit on training data only, leakage-safe)
- `model_*.joblib` — Trained models
- `selected_model.joblib` — The winning model
- `metrics.json` — Evaluation metrics and model selection

Model selection is DYNAMIC — the model with the highest PR-AUC wins. If retraining produces different results, the UI automatically reflects the new winner.

## Risk Score Policy
The Failure Risk Score (0-100) is an operational risk metric, NOT a calibrated probability.

| Level | Score Range | Action |
|---|---|---|
| LOW | < 20 | Normal operation |
| MEDIUM | 20 – 45 | Monitor |
| HIGH | 45 – 75 | Investigate |
| CRITICAL | ≥ 75 | Immediate attention |

## Firebase Configuration (Optional)
Set the environment variable `FIREBASE_CONFIG` with your Firebase web config JSON.
Without Firebase, history is stored locally in the browser (localStorage).

## Demo Workflow
1. Open http://localhost:5000
2. Click 'Try Demo Dataset' or 'Analyze Dataset'
3. The demo uses a bundled 1,000-record equipment telemetry file
4. View results → Click 'Diagnose' on any record → See SHAP explanation + 3D viewer + simulation

## Technical Stack
- **Backend**: Python / Flask
- **ML**: pandas, NumPy, scikit-learn, XGBoost, SHAP, Joblib
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (ES modules)
- **3D**: Three.js
- **Storage**: localStorage / Firebase Firestore (optional)

## Limitations
- Maximum 1,000 records per analysis session
- Training uses the full 10,000-row AI4I dataset
- 3D model is a conceptual visualization, not CAD-accurate
- Risk scores are operational thresholds, not calibrated probabilities
- Traditional ML only — no deep learning
- No IoT/hardware integration
- Firebase is optional; without it, history is session-local

---
*Decision support for maintenance planning — not a guaranteed engineering verdict.*
