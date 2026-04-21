import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib

# 1. Încarcă datele din fișierul Excel aflat în același folder
data = pd.read_excel("Set de date.xlsx", sheet_name=0)
data.columns = data.columns.str.strip()

# 2. Target și features (numele exacte din Excel)
target = "Stress_Level"
features = [
    "Coffee_Intake_Week",
    "Caffeine_mg_Week",
    "Sleep_Hours_Week",
    "Sleep_Quality",
    "Physical_Activity_Hours_Week",
    "Age",
    "Gender",
    "Smoking",
    "Alcohol_Consumption",
]

data = data.dropna(subset=[target])

X = data[features]
y = data[target]

numeric_features = [
    "Coffee_Intake_Week",
    "Caffeine_mg_Week",
    "Sleep_Hours_Week",
    "Physical_Activity_Hours_Week",
    "Age",
]
categorical_features = [
    "Sleep_Quality",
    "Gender",
    "Smoking",
    "Alcohol_Consumption",
]

numeric_transformer = "passthrough"
categorical_transformer = OneHotEncoder(handle_unknown="ignore")

preprocess = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, numeric_features),
        ("cat", categorical_transformer, categorical_features),
    ]
)

clf = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight="balanced",
)

model = Pipeline(steps=[
    ("preprocess", preprocess),
    ("clf", clf),
])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model.fit(X_train, y_train)

joblib.dump(model, "stress_model_rf.joblib")
print("Model salvat ca stress_model_rf.joblib")
