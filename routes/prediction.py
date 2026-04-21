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

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/form", response_model=FormSubmissionResponse)
async def submit_form(
    req: FormSubmissionRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Submit form with symptoms and get risk score.
    Uses rule-based logic for symptom interpretation.
    """
    logger.info(f"[FORM DEBUG] Received FormSubmissionRequest for user {current_user['user_id']}")
    logger.info(f"[FORM DEBUG] Form data: coffee_cups={req.coffee_cups}, caffeine_mg={req.caffeine_mg}, sleep_hours={req.sleep_hours}, sleep_quality={req.sleep_quality}, activity_hours={req.activity_hours}, age={req.age}, gender={req.gender}, smoker={req.smoker}, alcohol={req.alcohol}")
    
    PredictionRepository.init_db()

    symptoms = [
        req.symptoms_palpitations_tremor,
        req.symptoms_insomnia,
        req.symptoms_agitation,
        req.symptoms_concentration,
        req.symptoms_headache,
        req.symptoms_digestive,
    ]

    symptom_score, message = MLService.calculate_symptom_score(symptoms)
    logger.info(f"[FORM DEBUG] Symptom score: {symptom_score}, message: {message}")

    # Compute ML prediction with all 9 features
    # Convert daily to weekly
    coffee_intake_week = req.coffee_cups * 7
    caffeine_mg_week = req.caffeine_mg * 7
    sleep_hours_week = req.sleep_hours * 7
    activity_hours_week = req.activity_hours
    
    logger.info(f"[FORM DEBUG] Weekly values: coffee={coffee_intake_week}, caffeine={caffeine_mg_week}, sleep={sleep_hours_week}, activity={activity_hours_week}")
    logger.info(f"[FORM DEBUG] ML input: sleep_quality={req.sleep_quality.value}, gender={req.gender.value}, smoker={req.smoker.value}, alcohol={req.alcohol.value}")

    ml_pred = MLService.predict_stress(
        coffee_intake_week=coffee_intake_week,
        caffeine_mg_week=caffeine_mg_week,
        sleep_hours_week=sleep_hours_week,
        sleep_quality=req.sleep_quality.value,
        activity_hours_week=activity_hours_week,
        age=req.age,
        gender=req.gender.value,
        smoking=req.smoker.value,
        alcohol=req.alcohol.value,
    )
    logger.info(f"[FORM DEBUG] ML prediction result: {ml_pred}")

    submission_id = PredictionRepository.save_prediction(
        user_id=current_user["user_id"],
        varsta=req.age,
        cesti_cafea_zi=req.coffee_cups,
        ore_somn=req.sleep_hours,
        nivel_stres=5,
        predictie_stres=ml_pred,
        symptom_score=symptom_score,
    )
    logger.info(f"[FORM DEBUG] Prediction saved with submission_id: {submission_id}")

    return FormSubmissionResponse(
        score=symptom_score,
        prediction=ml_pred,
        message=message,
        submission_id=submission_id,
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
