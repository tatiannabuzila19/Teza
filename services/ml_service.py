import joblib
import numpy as np
from config import MODEL_PATH
import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning)

class MLService:
    _model = None
    _model_loaded = False

    @classmethod
    def load_model(cls):
        """Lazy load the trained model with fallback."""
        if cls._model_loaded:
            return cls._model
        
        try:
            cls._model = joblib.load(MODEL_PATH)
            cls._model_loaded = True
            print("[ML SERVICE] Model loaded successfully")
            return cls._model
        except Exception as e:
            print(f"[ML SERVICE] Warning: Could not load model: {e}")
            print("[ML SERVICE] Falling back to rule-based prediction")
            cls._model = None
            cls._model_loaded = True
            return None

    @staticmethod
    def predict_stress(coffee_intake_week: float, caffeine_mg_week: float, sleep_hours_week: float,
                      sleep_quality: str, activity_hours_week: float, age: int,
                      gender: str, smoking: str, alcohol: str) -> float:
        """Use Random Forest model to predict stress level with all 9 features."""
        model = MLService.load_model()
        
        if model is None:
            print("[ML SERVICE] Using fallback rule-based prediction")
            # Fallback rule-based score
            score = (
                (coffee_intake_week / 20.0) * 0.3 +  # 30% weight: coffee intake
                (1.0 - (sleep_hours_week / 56.0)) * 0.3 +  # 30% weight: sleep deficit
                (activity_hours_week / 20.0) * 0.2 +  # 20% weight: activity
                (1.0 if smoking == "Yes" else 0.0) * 0.1 +  # 10% weight: smoking
                (1.0 if alcohol == "Yes" else 0.0) * 0.1  # 10% weight: alcohol
            )
            return float(min(1.0, max(0.0, score)))
        
        try:
            # Prepare feature array in the exact order the model expects
            features = np.array([[
                coffee_intake_week,      # Coffee_Intake_Week
                caffeine_mg_week,        # Caffeine_mg_Week
                sleep_hours_week,        # Sleep_Hours_Week
                sleep_quality,           # Sleep_Quality (categorical)
                activity_hours_week,     # Physical_Activity_Hours_Week
                age,                     # Age
                gender,                  # Gender (categorical)
                smoking,                 # Smoking (categorical)
                alcohol,                 # Alcohol_Consumption (categorical)
            ]])
            
            print(f"[ML SERVICE] Predicting with 9 features: coffee_week={coffee_intake_week}, caffeine_week={caffeine_mg_week}, sleep_week={sleep_hours_week}, quality={sleep_quality}, activity={activity_hours_week}, age={age}, gender={gender}, smoking={smoking}, alcohol={alcohol}")
            prediction = model.predict(features)[0]
            print(f"[ML SERVICE] ML Prediction result: {prediction}")
            return float(prediction)
        except Exception as e:
            print(f"[ML SERVICE] Prediction error: {e}. Using fallback.")
            # Fallback if prediction fails
            score = (
                (coffee_intake_week / 20.0) * 0.3 +
                (1.0 - (sleep_hours_week / 56.0)) * 0.3 +
                (activity_hours_week / 20.0) * 0.2 +
                (1.0 if smoking == "Yes" else 0.0) * 0.1 +
                (1.0 if alcohol == "Yes" else 0.0) * 0.1
            )
            return float(min(1.0, max(0.0, score)))

    @staticmethod
    def calculate_symptom_score(symptoms: list) -> tuple:
        """Calculate symptom-based risk score (0–1) and interpret it."""
        max_per_symptom = 4
        score_raw = sum(symptoms)
        score = score_raw / (max_per_symptom * len(symptoms)) if symptoms else 0

        if score < 0.33:
            message = "Risc scăzut asociat consumului de cafea."
        elif score < 0.66:
            message = "Risc moderat, este bine să monitorizezi consumul."
        else:
            message = "Risc crescut, e recomandată reducerea consumului și consult medical."

        return score, message
