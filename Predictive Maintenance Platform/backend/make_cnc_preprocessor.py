import joblib
from sklearn.preprocessing import StandardScaler
import numpy as np

# Create dummy scaler for AI4I
scaler = StandardScaler()
# Fit with dummy data matching AI4I means
dummy_data = np.array([
    [300.0, 310.0, 1500.0, 40.0, 100.0],
    [298.0, 308.0, 1400.0, 30.0, 50.0],
    [302.0, 312.0, 1600.0, 50.0, 150.0]
])
scaler.fit(dummy_data)
joblib.dump(scaler, 'backend/ml_artifacts/preprocessor_cnc.joblib')
print("Created preprocessor_cnc.joblib")
