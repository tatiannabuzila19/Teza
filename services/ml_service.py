import joblib
import pandas as pd
import numpy as np
from config import MODEL_PATH, GENDER_OPTIONS, COUNTRY_OPTIONS, OCCUPATION_OPTIONS, SLEEP_QUALITY_OPTIONS, HEALTH_ISSUES_OPTIONS
import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning)

class MLService:
    _model = None
    _model_loaded = False

    @classmethod
    def load_model(cls):
        """Lazy load the trained model."""
        if cls._model_loaded:
            return cls._model
        
        try:
            cls._model = joblib.load(MODEL_PATH)
            cls._model_loaded = True
            print(f"[ML SERVICE] ✓ Model loaded successfully from {MODEL_PATH}")
            return cls._model
        except Exception as e:
            print(f"[ML SERVICE] ✗ Could not load model: {e}")
            cls._model = None
            cls._model_loaded = True
            return None

    @staticmethod
    def calculate_bmi(height_cm: int, weight_kg: float) -> float:
        """Calculate BMI from height and weight."""
        height_m = height_cm / 100.0
        bmi = weight_kg / (height_m ** 2)
        return round(bmi, 1)

    @staticmethod
    def _safe_string(val) -> str:
        """
        Helper method to prevent the 'ufunc isnan' error in OneHotEncoder.
        Ensures categorical values are strictly strings and handles None/NaNs.
        """
        if val is None or pd.isna(val):
            return "Missing"
        return str(val).strip()

    @staticmethod
    def _translate_to_model_lang(feature: str, val: str) -> str:
        """
        Translates Romanian form inputs to the English terms the model expects.
        This prevents OneHotEncoder from treating valid inputs as "Unknown".
        """
        val = MLService._safe_string(val)
        
        translations = {
            'Gender': {
                'Masculin': 'Male', 
                'Feminin': 'Female',
                'Altul': 'Other'
            },
            'Sleep_Quality': {
                'Scăzut': 'Poor',
                'Slab': 'Poor',
                'Mediu': 'Medium',
                'Bun': 'Good',
                'Excelent': 'Excellent'
            },
            'Health_Issues': {
                'Niciunul': 'None',
                'Moderate': 'Moderate', # Handled "Moderate" from your form testing
                'Severe': 'Severe',     # Added "Severe" from your latest test
                'Da': 'Yes',
                'Nu': 'No'
            },
            'Occupation': {
                'Birou': 'Office',
                'Student': 'Student',
                'Muncă fizică': 'Physical',
                'Fizic': 'Physical',
                'Altul': 'Other'
            }
        }
        
        if feature in translations and val in translations[feature]:
            return translations[feature][val]
        
        return val

    @staticmethod
    def predict_stress(
        coffee_cups: int,
        sleep_hours: float,
        sleep_quality: str,
        activity_hours: float,
        height_cm: int,
        weight_kg: float,
        heart_rate: int,
        age: int,
        gender: str,
        occupation: str,
        smoking: str,
        alcohol: str,
        health_issues: str,
        country: str = "Romania",
    ) -> tuple:
        """
        Predict stress level using the trained Random Forest model.
        Returns (prediction_score, category, details, message)
        """
        model = MLService.load_model()
        
        if model is None:
            print(f"[ML SERVICE] ✗ Model not available, using fallback")
            return (5.0, "Moderat", {"error": "Model not loaded"}, "Model indisponibil. Încercați din nou.")
        
        try:
            # Calculate derived features
            coffee_week = float(coffee_cups * 7)
            caffeine_week = float(coffee_cups * 7 * 95)  # ~95mg per cup
            sleep_week = float(sleep_hours * 7)
            bmi = float(MLService.calculate_bmi(height_cm, weight_kg))
            
            # Convert binary choices to numeric (0/1) safely
            smoking_encoded = 1 if MLService._safe_string(smoking).lower() in ["da", "1", "yes"] else 0
            alcohol_encoded = 1 if MLService._safe_string(alcohol).lower() in ["da", "1", "yes"] else 0
            
            # Apply translations from Romanian to English for the model
            mapped_gender = MLService._translate_to_model_lang('Gender', gender)
            mapped_sleep = MLService._translate_to_model_lang('Sleep_Quality', sleep_quality)
            mapped_health = MLService._translate_to_model_lang('Health_Issues', health_issues)
            mapped_occupation = MLService._translate_to_model_lang('Occupation', occupation)
            mapped_country = MLService._safe_string(country)
            
            # Create feature DataFrame with string categories the model understands
            features_df = pd.DataFrame({
                'Age': [float(age)],
                'Gender': [mapped_gender],
                'Country': [mapped_country],
                'Coffee_Intake_Week': [coffee_week],
                'Caffeine_mg_Week': [caffeine_week],
                'Sleep_Hours_Week': [sleep_week],
                'Sleep_Quality': [mapped_sleep],
                'BMI': [bmi],
                'Heart_Rate': [float(heart_rate)],
                'Physical_Activity_Hours_Week': [float(activity_hours)],
                'Health_Issues': [mapped_health],
                'Occupation': [mapped_occupation],
                'Smoking': [smoking_encoded],
                'Alcohol_Consumption': [alcohol_encoded],
            })
            
            print(f"\n[ML SERVICE] ========== STRESS PREDICTION ==========")
            print(f"[ML SERVICE] Input features (14 total):")
            for col in features_df.columns:
                print(f"  - {col}: {features_df[col].values[0]} ({features_df[col].dtype})")
            print(f"[ML SERVICE] Model type: {type(model).__name__}")
            
            # Get probabilities for refined prediction
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(features_df)[0]
                classes = model.classes_
                print(f"[ML SERVICE] Prediction classes: {classes}")
                print(f"[ML SERVICE] Prediction probabilities: {proba}")
                
                # Map classes to stress levels on a 1-10 scale
                class_to_stress = {}
                for idx, cls in enumerate(classes):
                    cls_str = str(cls).lower()
                    if cls_str == 'low' or cls_str == 'scăzut':
                        class_to_stress[idx] = 1.5  # Base score for Low
                    elif cls_str == 'medium' or cls_str == 'moderat':
                        class_to_stress[idx] = 5.0  # Base score for Medium
                    elif cls_str == 'high' or cls_str == 'ridicat':
                        class_to_stress[idx] = 9.5  # Base score for High
                    else:
                        class_to_stress[idx] = 5.0
                
                # Calculate weighted score (math will naturally cap around 9.4-9.5)
                stress_score = sum(class_to_stress.get(idx, 5.0) * prob for idx, prob in enumerate(proba))
                
                # Ensure the score never perfectly exceeds 10 or drops below 0 just in case
                stress_score = max(1.0, min(10.0, stress_score))
                print(f"[ML SERVICE] Weighted stress score: {stress_score:.2f}/10")
            else:
                # Fallback to direct prediction
                raw_pred = model.predict(features_df)[0]
                print(f"[ML SERVICE] Raw prediction: {raw_pred}")
                pred_map = {'Low': 1.5, 'Medium': 5.0, 'High': 9.5}
                stress_score = pred_map.get(str(raw_pred).title(), 5.0)
                print(f"[ML SERVICE] Mapped prediction: {stress_score}/10")
            
            # Categorize result
            if stress_score < 3.5:
                category = "Scăzut"
            elif stress_score < 7.0:
                category = "Moderat"
            else:
                category = "Ridicat"
            
            # Generate message
            if stress_score < 3.5:
                message = "Stres scăzut. Continuă cu activitățile tale normale și mențineți un stil de viață sănătos."
            elif stress_score < 7.0:
                message = "Stres moderat. Încearcă să reduci consumul de cafea și să dormi mai mult."
            else:
                message = "Stres ridicat. Se recomandă reducerea consumului de cafea și consultarea unui specialist medical."
            
            details = {
                'bmi': bmi,
                'height_cm': height_cm,
                'weight_kg': weight_kg,
                'heart_rate': heart_rate,
                'caffeine_week': caffeine_week,
                'sleep_week': sleep_week,
            }
            
            print(f"[ML SERVICE] ✓ Prediction: {stress_score:.2f}/10 ({category})")
            print(f"[ML SERVICE] =============================================\n")
            
            return (float(stress_score), category, details, message)
            
        except Exception as e:
            print(f"[ML SERVICE] ✗ Prediction error: {e}")
            import traceback
            traceback.print_exc()
            return (5.0, "Moderat", {"error": str(e)}, "Eroare în predicție. Încercați din nou.")