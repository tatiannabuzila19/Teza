import joblib
import numpy as np
import pandas as pd
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
            # Create DataFrame with correct column names matching trained model
            features_df = pd.DataFrame({
                'Coffee_Intake_Week': [coffee_intake_week],
                'Caffeine_mg_Week': [caffeine_mg_week],
                'Sleep_Hours_Week': [sleep_hours_week],
                'Sleep_Quality': [sleep_quality],
                'Physical_Activity_Hours_Week': [activity_hours_week],
                'Age': [age],
                'Gender': [gender],
                'Smoking': [smoking],
                'Alcohol_Consumption': [alcohol],
            })
            
            print(f"\n[ML SERVICE] ========== PREDICTION DEBUG ==========")
            print(f"[ML SERVICE] Input DataFrame shape: {features_df.shape}")
            print(f"[ML SERVICE] DataFrame columns: {list(features_df.columns)}")
            print(f"[ML SERVICE] DataFrame data:")
            print(features_df.to_string())
            print(f"[ML SERVICE] Model type: {type(model).__name__}")
            print(f"[ML SERVICE] Predicting with 9 features:")
            print(f"  - Coffee week: {coffee_intake_week}, Caffeine week: {caffeine_mg_week}")
            print(f"  - Sleep: {sleep_hours_week}h ({sleep_quality}), Activity: {activity_hours_week}h")
            print(f"  - Demographics: Age {age}, {gender}")
            print(f"  - Lifestyle: Smoking={smoking}, Alcohol={alcohol}")
            
            raw_prediction = model.predict(features_df)[0]
            print(f"[ML SERVICE] Raw model prediction: '{raw_prediction}'")
            print(f"[ML SERVICE] Prediction type: {type(raw_prediction).__name__}")
            print(f"[ML SERVICE] Prediction repr: {repr(raw_prediction)}")
            
            # Also try predict_proba if available
            try:
                if hasattr(model, 'predict_proba'):
                    proba = model.predict_proba(features_df)[0]
                    classes = model.classes_
                    print(f"[ML SERVICE] Available classes: {classes}")
                    print(f"[ML SERVICE] Prediction probabilities: {proba}")
                    
                    # Map classes to numeric stress levels
                    class_to_stress = {
                        'Low': 2.5,
                        'Medium': 5.0,
                        'High': 7.5,
                    }
                    
                    # Calculate weighted stress score using probabilities
                    stress_score = sum(class_to_stress.get(cls, 5.0) * prob for cls, prob in zip(classes, proba))
                    print(f"[ML SERVICE] Calculated weighted stress score: {stress_score:.2f}/10")
                    print(f"[ML SERVICE] ==========================================\n")
                    return float(stress_score)
            except Exception as pe:
                print(f"[ML SERVICE] Could not use predict_proba: {pe}")
            
            # Handle both classifier (categorical) and regressor (numeric) predictions
            prediction_str = str(raw_prediction).strip()
            print(f"[ML SERVICE] Converted to string: '{prediction_str}'")
            
            # Map categorical predictions to numeric stress levels
            stress_mapping = {
                'Low': 2.5,          # Low stress = 2.5/10
                'Medium': 5.0,       # Medium stress = 5.0/10
                'High': 7.5,         # High stress = 7.5/10
            }
            
            if prediction_str in stress_mapping:
                numeric_pred = stress_mapping[prediction_str]
                print(f"[ML SERVICE] ✓ Matched categorical: '{prediction_str}' → {numeric_pred}/10")
                print(f"[ML SERVICE] ==========================================\n")
                return float(numeric_pred)
            else:
                # Try to convert directly to float if it's numeric
                try:
                    numeric_pred = float(raw_prediction)
                    # If prediction is 0-1 scale, convert to 0-10
                    if 0 <= numeric_pred <= 1:
                        numeric_pred = numeric_pred * 10
                        print(f"[ML SERVICE] ✓ Converted 0-1 scale to 0-10: {numeric_pred}/10")
                    else:
                        print(f"[ML SERVICE] ✓ Direct numeric prediction (already 0-10): {numeric_pred}/10")
                    print(f"[ML SERVICE] ==========================================\n")
                    return float(numeric_pred)
                except ValueError:
                    # Unknown prediction type, use fallback
                    print(f"[ML SERVICE] ⚠ Unknown prediction type: '{prediction_str}'")
                    print(f"[ML SERVICE] Available mappings: {list(stress_mapping.keys())}")
                    raise ValueError(f"Unknown prediction: {prediction_str}")
                
        except Exception as e:
            print(f"[ML SERVICE] ✗ Prediction error: {e}")
            print(f"[ML SERVICE] Using rule-based fallback prediction")
            
            # Fallback rule-based prediction
            score = (
                (coffee_intake_week / 20.0) * 0.3 +      # Coffee consumption
                (1.0 - (sleep_hours_week / 56.0)) * 0.3 +  # Sleep deficit
                (activity_hours_week / 20.0) * 0.2 +      # Physical activity
                (1.0 if smoking == "Yes" else 0.0) * 0.1 +  # Smoking
                (1.0 if alcohol == "Yes" else 0.0) * 0.1    # Alcohol
            )
            fallback_score = float(min(1.0, max(0.0, score)))
            print(f"[ML SERVICE] Fallback score: {fallback_score}")
            return fallback_score

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
