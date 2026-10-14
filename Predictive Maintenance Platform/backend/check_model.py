import joblib
m = joblib.load('backend/ml_artifacts/selected_model.joblib')
print(type(m))
