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
    def encode_categorical_feature(feature_name: str, value: str) -> int:
        """Encode categorical features to numeric values."""
        mapping = {
            'Gender': GENDER_OPTIONS,
            'Country': COUNTRY_OPTIONS,
            'Occupation': OCCUPATION_OPTIONS,
            'Sleep_Quality': SLEEP_QUALITY_OPTIONS,
            'Health_Issues': HEALTH_ISSUES_OPTIONS,
        }
        
        if feature_name not in mapping:
            print(f"[ML SERVICE] ⚠ Unknown feature: {feature_name}")
            return 0
        
        options = mapping[feature_name]
        encoded = options.get(value, 0)
        print(f"[ML SERVICE] Encoded {feature_name}='{value}' → {encoded}")
        return encoded

    @staticmethod
    def calculate_bmi(height_cm: int, weight_kg: float) -> float:
        """Calculate BMI from height and weight."""
        height_m = height_cm / 100.0
        bmi = weight_kg / (height_m ** 2)
        return round(bmi, 1)

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
            coffee_week = coffee_cups * 7
            caffeine_week = coffee_cups * 7 * 95  # ~95mg per cup
            sleep_week = sleep_hours * 7
            bmi = MLService.calculate_bmi(height_cm, weight_kg)
            
            # Convert binary choices to numeric (0/1)
            smoking_encoded = 1 if smoking == "Da" else 0
            alcohol_encoded = 1 if alcohol == "Da" else 0
            
            # Create feature DataFrame with correct column order for the model
            # Pass categorical features as ORIGINAL STRING VALUES (let model preprocessor handle encoding)
            features_df = pd.DataFrame({
                'Age': [float(age)],
                'Gender': [gender],  # Keep as string - model's preprocessor will encode
                'Country': [country],  # Keep as string
                'Coffee_Intake_Week': [float(coffee_week)],
                'Caffeine_mg_Week': [float(caffeine_week)],
                'Sleep_Hours_Week': [float(sleep_week)],
                'Sleep_Quality': [sleep_quality],  # Keep as string
                'BMI': [float(bmi)],
                'Heart_Rate': [float(heart_rate)],
                'Physical_Activity_Hours_Week': [float(activity_hours)],
                'Health_Issues': [health_issues],  # Keep as string
                'Occupation': [occupation],  # Keep as string
                'Smoking': [int(smoking_encoded)],
                'Alcohol_Consumption': [int(alcohol_encoded)],
            })
            
            print(f"\n[ML SERVICE] ========== STRESS PREDICTION ==========")
            print(f"[ML SERVICE] Input features (14 total):")
            print(f"[ML SERVICE] DataFrame columns: {list(features_df.columns)}")
            print(f"[ML SERVICE] DataFrame dtypes:\n{features_df.dtypes}")
            for col in features_df.columns:
                print(f"  - {col}: {features_df[col].values[0]} ({features_df[col].dtype})")
            print(f"[ML SERVICE] BMI (calculated): {bmi}")
            print(f"[ML SERVICE] Coffee/week: {coffee_week} cups, Caffeine/week: {caffeine_week}mg")
            print(f"[ML SERVICE] Sleep/week: {sleep_week}h, Activity/week: {activity_hours}h")
            print(f"[ML SERVICE] Model type: {type(model).__name__}")
            
            # Get probabilities for refined prediction
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(features_df)[0]
                classes = model.classes_
                print(f"[ML SERVICE] Prediction classes: {classes}")
                print(f"[ML SERVICE] Prediction probabilities: {proba}")
                
                # Map classes to stress levels
                class_to_stress = {}
                for idx, cls in enumerate(classes):
                    if cls == 'Low':
                        class_to_stress[idx] = 2.5
                    elif cls == 'Medium':
                        class_to_stress[idx] = 5.0
                    elif cls == 'High':
                        class_to_stress[idx] = 7.5
                    else:
                        class_to_stress[idx] = 5.0
                
                # Calculate weighted score
                stress_score = sum(class_to_stress.get(idx, 5.0) * prob for idx, prob in enumerate(proba))
                print(f"[ML SERVICE] Weighted stress score: {stress_score:.2f}/10")
            else:
                # Fallback to direct prediction
                raw_pred = model.predict(features_df)[0]
                print(f"[ML SERVICE] Raw prediction: {raw_pred}")
                pred_map = {'Low': 2.5, 'Medium': 5.0, 'High': 7.5}
                stress_score = pred_map.get(raw_pred, 5.0)
                print(f"[ML SERVICE] Mapped prediction: {stress_score}/10")
            
            # Categorize result
            if stress_score < 3.5:
                category = "Scăzut"
            elif stress_score < 6.5:
                category = "Moderat"
            else:
                category = "Ridicat"
            
            # Generate message
            if stress_score < 3.5:
                message = "Stres scăzut. Continuă cu activitățile tale normale și mențineți un stil de viață sănătos."
            elif stress_score < 6.5:
                message = "Stres moderat. Încearcă să reduce consumul de cafea și să dormi mai mult."
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

