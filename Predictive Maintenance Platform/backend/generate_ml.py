import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import json

np.random.seed(42)
N = 10000

families = ['Pump', 'Motor', 'Compressor', 'Gearbox', 'CNC', 'Turbine', 'Boiler', 'Generator', 'Fan', 'Transformer']

data = {
    'UDI': np.arange(1, N + 1),
    'Machine_Family': np.random.choice(families, N),
    'Age_Days': np.random.randint(10, 5000, N),
    'Power_kW': np.random.uniform(5, 500, N)
}

df = pd.DataFrame(data)

# Sensors
df['Sensor_Vibration_mm_s'] = np.random.normal(2.0, 1.0, N)
df['Sensor_Temperature_C'] = np.random.normal(50.0, 15.0, N)
df['Sensor_Pressure_bar'] = np.random.normal(5.0, 2.0, N)
df['Sensor_Current_A'] = df['Power_kW'] * np.random.normal(1.5, 0.2, N)
df['Sensor_Speed_RPM'] = np.random.normal(1500, 100, N)

# Induce failures based on realistic engineering limits
failure = np.zeros(N, dtype=int)
failure_mode = np.array(['None'] * N, dtype=object)

for i in range(N):
    fam = df.loc[i, 'Machine_Family']
    vib = df.loc[i, 'Sensor_Vibration_mm_s']
    temp = df.loc[i, 'Sensor_Temperature_C']
    press = df.loc[i, 'Sensor_Pressure_bar']
    curr = df.loc[i, 'Sensor_Current_A']
    age = df.loc[i, 'Age_Days']
    
    # Base probability of failure increases with age
    fail_prob = age / 50000.0
    
    # Overrides
    if vib > 8.0:
        failure[i] = 1
        failure_mode[i] = 'Bearing Degradation'
    elif temp > 95.0:
        failure[i] = 1
        failure_mode[i] = 'Overheating'
    elif fam in ['Pump', 'Compressor'] and press < 1.0:
        failure[i] = 1
        failure_mode[i] = 'Cavitation / Leak'
    elif curr > df.loc[i, 'Power_kW'] * 2.2:
        failure[i] = 1
        failure_mode[i] = 'Electrical Overload'
    elif np.random.random() < fail_prob:
        failure[i] = 1
        failure_mode[i] = 'Random Wear'
        
df['Machine_Failure'] = failure
df['Failure_Mode'] = failure_mode

# Save the rich dataset for the frontend
os.makedirs('frontend/assets/data', exist_ok=True)
df.to_csv('frontend/assets/data/demo-equipment-1000.csv', index=False)
print("Saved demo-equipment-1000.csv with realistic multi-machine data")

# Train ML Model
X = df.drop(['UDI', 'Machine_Failure', 'Failure_Mode'], axis=1)
y = df['Machine_Failure']

numeric_features = ['Age_Days', 'Power_kW', 'Sensor_Vibration_mm_s', 'Sensor_Temperature_C', 'Sensor_Pressure_bar', 'Sensor_Current_A', 'Sensor_Speed_RPM']
categorical_features = ['Machine_Family']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])

clf = Pipeline(steps=[('preprocessor', preprocessor),
                      ('classifier', GradientBoostingClassifier(n_estimators=100, random_state=42))])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
clf.fit(X_train, y_train)

score = clf.score(X_test, y_test)
print(f"Model Accuracy: {score:.3f}")

# Save the new model to backend/ml_artifacts
os.makedirs('backend/ml_artifacts', exist_ok=True)
joblib.dump(clf, 'backend/ml_artifacts/realistic_model.joblib')

# We must update the /api/analyze to use the new model, and we will do that next
print("Saved realistic_model.joblib")
