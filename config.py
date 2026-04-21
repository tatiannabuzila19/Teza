import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database paths
COFFEE_DB = os.getenv(
    "COFFEE_DB_PATH",
    "C:/Users/tatia/Desktop/Anul 3/Teza de licenta/coffee-risk-evaluator/coffee_data.db"
)
STRES_DB = os.getenv("STRES_DB_PATH", os.path.join(BASE_DIR, "stres.db"))

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ML Model
MODEL_PATH = os.getenv("MODEL_PATH", os.path.join(BASE_DIR, "stress_model_rf.joblib"))

# Validation ranges
AGE_MIN, AGE_MAX = 18, 100
COFFEE_CUPS_MIN, COFFEE_CUPS_MAX = 0, 20
SLEEP_HOURS_MIN, SLEEP_HOURS_MAX = 0, 24
SYMPTOM_MIN, SYMPTOM_MAX = 0, 4
