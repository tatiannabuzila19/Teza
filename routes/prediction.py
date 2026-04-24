from fastapi import APIRouter, Depends
from pydantic import ValidationError
import logging
from models.schemas import (
    FormSubmissionRequest, PredictionRequest,
    FormSubmissionResponse, PredictionResponse
)
from services.auth_service import get_current_user, require_role
from services.ml_service import MLService
from db.predictions import PredictionRepository
from db.evaluations import EvaluationRepository
from typing import List, Dict

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/form", response_model=FormSubmissionResponse)
async def submit_form(
    req: FormSubmissionRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Submit form with 14 features and get stress prediction with ML model.
    New model has 14 features: coffee_cups, sleep_hours, sleep_quality, activity_hours,
    height_cm, weight_kg, heart_rate, age, gender, country, occupation, smoking, alcohol, health_issues.
    """
    logger.info(f"[FORM DEBUG] Received FormSubmissionRequest for user {current_user['user_id']}")
    logger.info(f"[FORM DEBUG] Form data: coffee={req.coffee_cups}, sleep={req.sleep_hours}, sleep_quality={req.sleep_quality}, activity={req.activity_hours}")
    logger.info(f"[FORM DEBUG] Physical: height={req.height_cm}cm, weight={req.weight_kg}kg, heart_rate={req.heart_rate}bpm")
    logger.info(f"[FORM DEBUG] Personal: age={req.age}, gender={req.gender}, country={req.country}, occupation={req.occupation}")
    logger.info(f"[FORM DEBUG] Lifestyle: smoking={req.smoking}, alcohol={req.alcohol}, health_issues={req.health_issues}")
    
    PredictionRepository.init_db()

    # Call ML service with all 14 features
    # Returns tuple: (stress_score, category, details_dict, message)
    try:
        stress_score, category, details, message = MLService.predict_stress(
            coffee_cups=req.coffee_cups,
            sleep_hours=req.sleep_hours,
            sleep_quality=req.sleep_quality.value,
            activity_hours=req.activity_hours,
            height_cm=req.height_cm,
            weight_kg=req.weight_kg,
            heart_rate=req.heart_rate,
            age=req.age,
            gender=req.gender.value,
            occupation=req.occupation.value,
            smoking=req.smoking.value,
            alcohol=req.alcohol.value,
            health_issues=req.health_issues.value,
            country=req.country,
        )
        logger.info(f"[FORM DEBUG] ML prediction: stress={stress_score:.2f}/10, category={category}, message={message}")
    except Exception as e:
        logger.error(f"[FORM DEBUG] ML prediction error: {e}")
        stress_score = 5.0
        category = "Moderat"
        message = "Eroare în predicție. Încercați din nou."
        details = {}

    submission_id = PredictionRepository.save_prediction(
        user_id=current_user["user_id"],
        varsta=req.age,
        cesti_cafea_zi=req.coffee_cups,
        ore_somn=req.sleep_hours,
        nivel_stres=5,
        predictie_stres=stress_score,
        symptom_score=stress_score / 10.0,
    )
    logger.info(f"[FORM DEBUG] Prediction saved with submission_id: {submission_id}")

    # Also save to evaluations table
    EvaluationRepository.init_db()
    
    # Map Romanian categories to English
    stress_level_map = {
        "Scăzut": "Low",
        "Moderat": "Medium", 
        "Ridicat": "High"
    }
    stress_level = stress_level_map.get(category, "Medium")
    
    # Calculate BMI
    bmi = MLService.calculate_bmi(req.height_cm, req.weight_kg)
    
    evaluation_id = EvaluationRepository.save_evaluation(
        user_id=current_user["user_id"],
        coffee_intake_day=req.coffee_cups,
        sleep_hours_night=req.sleep_hours,
        bmi=bmi,
        heart_rate=req.heart_rate,
        stress_level=stress_level,
        stress_score=stress_score,
        physical_activity=req.activity_hours,
    )
    logger.info(f"[FORM DEBUG] Evaluation saved with evaluation_id: {evaluation_id}")

    return FormSubmissionResponse(
        prediction=stress_score,
        prediction_category=category,
        message=message,
        submission_id=submission_id,
        details=details,
    )

@router.post("/predict", response_model=PredictionResponse)
async def predict_endpoint(
    req: PredictionRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Use trained Random Forest model to predict stress level.
    """
    PredictionRepository.init_db()

    ml_pred = MLService.predict_stress(
        req.varsta, req.cesti_cafea_zi, req.ore_somn, req.nivel_stres
    )

    submission_id = PredictionRepository.save_prediction(
        user_id=current_user["user_id"],
        varsta=req.varsta,
        cesti_cafea_zi=req.cesti_cafea_zi,
        ore_somn=req.ore_somn,
        nivel_stres=req.nivel_stres,
        predictie_stres=ml_pred,
        symptom_score=0.0,
    )

    return PredictionResponse(
        predictie_stres=ml_pred,
        submission_id=submission_id,
    )

@router.get("/my-predictions")
async def get_my_predictions(current_user: dict = Depends(get_current_user)):
    """Fetch all predictions for the logged-in user."""
    return PredictionRepository.get_user_predictions(current_user["user_id"])

@router.get("/api/history")
async def get_history(current_user: dict = Depends(get_current_user)):
    """Fetch evaluation history for the logged-in user."""
    evaluations = EvaluationRepository.get_user_evaluations(current_user["user_id"])
    weekly_data = EvaluationRepository.get_user_evaluations_last_week(current_user["user_id"])
    weekly_comparison = EvaluationRepository.get_weekly_comparison(current_user["user_id"])
    
    return {
        "evaluations": evaluations,
        "weekly_data": weekly_data,
        "weekly_comparison": weekly_comparison
    }
