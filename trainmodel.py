import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.ensemble import RandomForestClassifier
import joblib

# Load dataset
df = pd.read_excel("matatag-dataset.xlsx")

# Group all three task fields
grouped = df.groupby(['pattern_score', 'subtraction_score', 'income_bracket']).agg({
    'task_title': list,
    'task_details': list,
    'task_objective': list
}).reset_index()

# Store mapping separately
grouped.to_pickle("grouped_tasks.pkl")

# Encode only the titles for model
mlb = MultiLabelBinarizer()
y = mlb.fit_transform(grouped['task_title'])

X = grouped[['pattern_score', 'subtraction_score', 'income_bracket']]
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

joblib.dump(model, "model.pkl")
joblib.dump(mlb, "mlb.pkl")
