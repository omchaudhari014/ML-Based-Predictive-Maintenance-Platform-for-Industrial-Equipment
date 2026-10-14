import pandas as pd
import numpy as np
import os
import json
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix, roc_curve

df = pd.read_csv('frontend/assets/data/demo-equipment-1000.csv')
FEATURE_COLS = ['Machine_Family', 'Age_Days', 'Power_kW', 'Sensor_Vibration_mm_s', 'Sensor_Temperature_C', 'Sensor_Pressure_bar', 'Sensor_Current_A', 'Sensor_Speed_RPM']

X = df[FEATURE_COLS]
y = df['Machine_Failure']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Numeric and categorical pipelines
num_cols = [c for c in FEATURE_COLS if c != 'Machine_Family']
cat_cols = ['Machine_Family']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), num_cols),
        ('cat', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1), cat_cols)
    ]
)

# Fit preprocessor
preprocessor.fit(X_train)
X_train_trans = preprocessor.transform(X_train)
X_test_trans = preprocessor.transform(X_test)

joblib.dump(preprocessor, 'backend/ml_artifacts/preprocessor.joblib')

models = [
    {"id": "lr", "name": "Logistic Regression", "model": LogisticRegression(max_iter=1000, random_state=42)},
    {"id": "rf", "name": "Random Forest", "model": RandomForestClassifier(n_estimators=100, random_state=42)},
    {"id": "gb", "name": "Gradient Boosting", "model": GradientBoostingClassifier(random_state=42)},
    {"id": "xgb", "name": "XGBoost", "model": XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)}
]

metrics_list = []
best_prauc = -1
best_model_id = "xgb"
best_model_name = "XGBoost"

for m in models:
    clf = m['model']
    clf.fit(X_train_trans, y_train)
    joblib.dump(clf, f"backend/ml_artifacts/model_{m['id']}.joblib")
    
    y_pred = clf.predict(X_test_trans)
    y_prob = clf.predict_proba(X_test_trans)[:, 1]
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)
    
    cm = confusion_matrix(y_test, y_pred).tolist()
    
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    
    # Downsample ROC points for frontend JSON size
    roc_points = []
    if len(fpr) > 20:
        indices = np.linspace(0, len(fpr)-1, 20).astype(int)
        for idx in indices:
            roc_points.append([round(float(fpr[idx]), 3), round(float(tpr[idx]), 3)])
    else:
        for f, t in zip(fpr, tpr):
            roc_points.append([round(float(f), 3), round(float(t), 3)])
            
    if pr_auc > best_prauc:
        best_prauc = pr_auc
        best_model_id = m['id']
        best_model_name = m['name']
        
    metrics_list.append({
        "id": m['id'],
        "name": m['name'],
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "confusion": cm,
        "roc": roc_points
    })

output_metrics = {
    "selected_model": best_model_name,
    "selected_key": best_model_id,
    "rule": "Selected based on highest PR-AUC for imbalanced failure detection.",
    "feature_names": {
        "feature_columns": FEATURE_COLS,
        "mode_columns": ["Failure_Mode"],
        "id_columns": ["UDI"]
    },
    "models": metrics_list
}

with open('backend/ml_artifacts/metrics.json', 'w') as f:
    json.dump(output_metrics, f, indent=2)

print(f"Trained all models. Best model: {best_model_name} (PR-AUC: {best_prauc:.4f})")
