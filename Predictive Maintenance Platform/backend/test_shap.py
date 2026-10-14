import shap
import joblib, pandas as pd
model = joblib.load('ml_artifacts/selected_model.joblib')
pre = joblib.load('ml_artifacts/preprocessor.joblib')
df = pd.DataFrame([{'Air temperature [K]': 298.1, 'Process temperature [K]': 308.6, 'Rotational speed [rpm]': 1551, 'Torque [Nm]': 42.8, 'Tool wear [min]': 0}])
X = pre.transform(df)
explainer = shap.TreeExplainer(model)
sv = explainer.shap_values(X)
print('SHAP VALUES:', sv)
