import joblib

pipeline = joblib.load('backend/ml_artifacts/model_realistic.joblib')
joblib.dump(pipeline.named_steps['preprocessor'], 'backend/ml_artifacts/preprocessor.joblib')
joblib.dump(pipeline.named_steps['classifier'], 'backend/ml_artifacts/model_realistic.joblib')
print("Separated preprocessor and classifier")
