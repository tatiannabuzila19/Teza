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
HEIGHT_MIN, HEIGHT_MAX = 120, 220  # cm
WEIGHT_MIN, WEIGHT_MAX = 30, 200   # kg
HEART_RATE_MIN, HEART_RATE_MAX = 40, 200  # bpm
ACTIVITY_MIN, ACTIVITY_MAX = 0, 30  # hours/week

# Categorical feature encodings
GENDER_OPTIONS = {
    'Masculin': 'Male',
    'Feminin': 'Female',
    'Altul': 'Other'
}

COUNTRY_OPTIONS = {
    'România': 0,
    'Austria': 1,
    'Belgia': 2,
    'Bulgaria': 3,
    'Croația': 4,
    'Cipru': 5,
    'Cehia': 6,
    'Danemarca': 7,
    'Estonia': 8,
    'Finlanda': 9,
    'Franța': 10,
    'Germania': 11,
    'Grecia': 12,
    'Ungaria': 13,
    'Irlanda': 14,
    'Italia': 15,
    'Letonia': 16,
    'Lituania': 17,
    'Luxemburg': 18,
    'Malta': 19,
    'Olanda': 20,
    'Polonia': 21,
    'Portugalia': 22,
    'Slovacia': 23,
    'Slovenia': 24,
    'Spania': 25,
    'Suedia': 26
}

OCCUPATION_OPTIONS = {
    'Student': 0,
    'Birou': 1,
    'Sănătate': 2,
    'Servicii': 3,
    'Altul': 4
}

SLEEP_QUALITY_OPTIONS = {
    'Excelent': 0,
    'Bun': 1,
    'Mediu': 2,
    'Slab': 3
}

HEALTH_ISSUES_OPTIONS = {
    'Niciunul': 0,
    'Ușoare': 1,
    'Moderate': 2,
    'Severe': 3
}
