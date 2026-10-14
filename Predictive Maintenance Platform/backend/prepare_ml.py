"""prepare_ml.py — Train the predictive-maintenance ML pipeline.

Trains four traditional ML models on the UCI AI4I 2020 dataset (10,000 rows),
evaluates them, selects the best by PR-AUC, and saves all artifacts to
ml_artifacts/.  The preprocessing pipeline is fit ONLY on training data
(leakage-safe).

Usage:
    python prepare_ml.py

Artifacts produced:
    ml_artifacts/preprocessor.joblib   — fitted ColumnTransformer (imputer+scaler)
    ml_artifacts/model_<name>.joblib   — each trained model
    ml_artifacts/selected_model.joblib — the winning model (convenience copy)
    ml_artifacts/metrics.json          — evaluation metrics + selected_model name
    ml_artifacts/feature_names.json    — ordered feature list used by the pipeline
    ml_artifacts/label_encoder.json    — target column info
"""

import json
import os
import sys
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
    auc,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

warnings.filterwarnings("ignore", category=FutureWarning)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "data", "ai4i2020.csv")
ARTIFACTS_DIR = os.path.join(HERE, "ml_artifacts")

# The five numeric sensor features used for prediction.
FEATURE_COLS = [
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]

TARGET_COL = "Machine failure"

# Failure-mode flag columns (observed labels, NOT predicted by the risk model).
MODE_COLS = ["TWF", "HDF", "PWF", "OSF", "RNF"]

# Equipment-identity columns (used at inference time, not for training).
ID_COLS = ["UDI", "Product ID", "Type"]


def load_data():
    """Load and validate the AI4I dataset."""
    if not os.path.isfile(DATA_PATH):
        print(f"ERROR: Dataset not found at {DATA_PATH}", file=sys.stderr)
        print("Run  python scripts/fetch_dataset.py  first.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns from {DATA_PATH}")

    # Validate required columns.
    missing = [c for c in FEATURE_COLS + [TARGET_COL] if c not in df.columns]
    if missing:
        print(f"ERROR: Missing columns: {missing}", file=sys.stderr)
        sys.exit(1)

    print(f"Target distribution:\n{df[TARGET_COL].value_counts().to_string()}")
    print(f"Failure rate: {df[TARGET_COL].mean():.3f}")
    return df


def build_preprocessor():
    """Build the leakage-safe preprocessing pipeline.

    This is fit ONLY on training data.  At inference time, the same fitted
    transformer is applied to new data — no statistics are ever computed
    from the inference batch.
    """
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    preprocessor = ColumnTransformer(
        transformers=[("num", numeric_pipeline, FEATURE_COLS)],
        remainder="drop",
    )
    return preprocessor


def build_models():
    """Return a dict of model_key → (display_name, estimator)."""
    return {
        "logistic_regression": (
            "Logistic Regression",
            LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
        ),
        "random_forest": (
            "Random Forest",
            RandomForestClassifier(
                n_estimators=200, max_depth=10, class_weight="balanced",
                random_state=42, n_jobs=-1,
            ),
        ),
        "gradient_boosting": (
            "Gradient Boosting",
            GradientBoostingClassifier(
                n_estimators=200, max_depth=5, learning_rate=0.1,
                random_state=42,
            ),
        ),
        "xgboost": (
            "XGBoost",
            XGBClassifier(
                n_estimators=200, max_depth=5, learning_rate=0.1,
                scale_pos_weight=9,  # approximate class imbalance ratio
                use_label_encoder=False, eval_metric="logloss",
                random_state=42, n_jobs=-1,
            ),
        ),
    }


def evaluate_model(model, X_test, y_test):
    """Compute all evaluation metrics for a fitted model."""
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    # ROC curve
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    roc_auc = roc_auc_score(y_test, y_proba)

    # PR curve
    prec_curve, rec_curve, _ = precision_recall_curve(y_test, y_proba)
    pr_auc = auc(rec_curve, prec_curve)

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    # Subsample curve points for JSON (keep it small).
    def subsample(xs, ys, n=15):
        if len(xs) <= n:
            return list(zip(round_list(xs), round_list(ys)))
        idx = np.linspace(0, len(xs) - 1, n, dtype=int)
        return list(zip(round_list(xs[idx]), round_list(ys[idx])))

    def round_list(arr):
        return [round(float(v), 4) for v in arr]

    return {
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "rocAuc": round(float(roc_auc), 4),
        "prAuc": round(float(pr_auc), 4),
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "confusion": {"tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn)},
        "roc": subsample(fpr, tpr),
        "pr": subsample(rec_curve, prec_curve),
    }


def main():
    print("=" * 60)
    print("ML Pipeline — Predictive Maintenance Platform")
    print("=" * 60)

    # 1. Load data.
    df = load_data()

    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    # 2. Train/test split (stratified).
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )
    print(f"\nTrain: {len(X_train)} rows | Test: {len(X_test)} rows")
    print(f"Train failure rate: {y_train.mean():.3f} | Test failure rate: {y_test.mean():.3f}")

    # 3. Fit preprocessor on TRAINING data only (leakage-safe).
    preprocessor = build_preprocessor()
    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)
    print(f"Preprocessing fitted on training data: {X_train_processed.shape}")

    # 4. Train and evaluate all models.
    models = build_models()
    results = []
    fitted_models = {}

    for key, (name, estimator) in models.items():
        print(f"\nTraining {name}...")
        estimator.fit(X_train_processed, y_train)
        metrics = evaluate_model(estimator, X_test_processed, y_test)
        metrics["name"] = name
        metrics["key"] = key
        results.append(metrics)
        fitted_models[key] = estimator
        print(f"  Precision={metrics['precision']:.3f}  Recall={metrics['recall']:.3f}  "
              f"F1={metrics['f1']:.3f}  ROC-AUC={metrics['rocAuc']:.3f}  "
              f"PR-AUC={metrics['prAuc']:.3f}  Accuracy={metrics['accuracy']:.3f}")

    # 5. Select the best model by PR-AUC (dynamic, never hardcoded).
    best = max(results, key=lambda m: m["prAuc"])
    selected_key = best["key"]
    selected_name = best["name"]
    print(f"\n>>> Selected model: {selected_name} (PR-AUC = {best['prAuc']:.4f})")

    # 6. Save artifacts.
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    # Preprocessor.
    joblib.dump(preprocessor, os.path.join(ARTIFACTS_DIR, "preprocessor.joblib"))
    print(f"Saved preprocessor.joblib")

    # All models.
    for key, estimator in fitted_models.items():
        path = os.path.join(ARTIFACTS_DIR, f"model_{key}.joblib")
        joblib.dump(estimator, path)
        print(f"Saved model_{key}.joblib")

    # Selected model convenience copy.
    joblib.dump(fitted_models[selected_key],
                os.path.join(ARTIFACTS_DIR, "selected_model.joblib"))

    # Feature names.
    feature_info = {
        "feature_columns": FEATURE_COLS,
        "target_column": TARGET_COL,
        "mode_columns": MODE_COLS,
        "id_columns": ID_COLS,
    }
    with open(os.path.join(ARTIFACTS_DIR, "feature_names.json"), "w") as f:
        json.dump(feature_info, f, indent=2)

    # Metrics (the UI reads this to display model comparison).
    metrics_output = {
        "selected_model": selected_name,
        "selected_key": selected_key,
        "selection_criterion": "highest PR-AUC",
        "selection_criterion_key": "prAuc",
        "class_imbalance_note": (
            "With roughly a 9:1 healthy-to-failure ratio, a model that predicts "
            "'no failure' for every record would still score ~0.90 accuracy while "
            "catching zero failures. That is why the comparison leads with Precision, "
            "Recall, F1 and PR-AUC, and de-emphasises Accuracy."
        ),
        "risk_policy_note": (
            "Risk levels (LOW/MEDIUM/HIGH/CRITICAL) are an Operational Risk Policy, "
            "not learned probability thresholds. The model outputs a Failure Risk Score "
            "(0-100) which is mapped to risk levels at fixed operational thresholds: "
            "LOW < 20, MEDIUM 20-45, HIGH 45-75, CRITICAL >= 75."
        ),
        "models": results,
        "training_rows": len(X_train),
        "test_rows": len(X_test),
        "feature_count": len(FEATURE_COLS),
    }
    with open(os.path.join(ARTIFACTS_DIR, "metrics.json"), "w") as f:
        json.dump(metrics_output, f, indent=2)
    print(f"Saved metrics.json (selected_model: {selected_name})")

    print("\n" + "=" * 60)
    print("ML Pipeline complete. All artifacts saved to ml_artifacts/")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
