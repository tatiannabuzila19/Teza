from pydantic import BaseModel, Field, validator
from typing import Optional
from enum import Enum
from config import AGE_MIN, AGE_MAX, COFFEE_CUPS_MIN, COFFEE_CUPS_MAX, SLEEP_HOURS_MIN, SLEEP_HOURS_MAX, SYMPTOM_MIN, SYMPTOM_MAX

class Gender(str, Enum):
    MALE = "M"
    FEMALE = "F"
    OTHER = "Other"

class BooleanChoice(str, Enum):
    YES = "Yes"
    NO = "No"

class SleepQuality(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    ANALYST = "analyst"

# Authentication
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    role: str

# Form submission
class FormSubmissionRequest(BaseModel):
    coffee_cups: int = Field(..., ge=COFFEE_CUPS_MIN, le=COFFEE_CUPS_MAX)
    caffeine_mg: int = Field(..., ge=0, le=2000)
    sleep_hours: float = Field(..., ge=SLEEP_HOURS_MIN, le=SLEEP_HOURS_MAX)
    sleep_quality: SleepQuality
    activity_hours: float = Field(..., ge=0, le=24)
    age: int = Field(..., ge=AGE_MIN, le=AGE_MAX)
    gender: Gender
    smoker: BooleanChoice
    alcohol: BooleanChoice
    symptoms_palpitations_tremor: int = Field(..., ge=SYMPTOM_MIN, le=SYMPTOM_MAX)
    symptoms_insomnia: int = Field(..., ge=SYMPTOM_MIN, le=SYMPTOM_MAX)
    symptoms_agitation: int = Field(..., ge=SYMPTOM_MIN, le=SYMPTOM_MAX)
    symptoms_concentration: int = Field(..., ge=SYMPTOM_MIN, le=SYMPTOM_MAX)
    symptoms_headache: int = Field(..., ge=SYMPTOM_MIN, le=SYMPTOM_MAX)
    symptoms_digestive: int = Field(..., ge=SYMPTOM_MIN, le=SYMPTOM_MAX)

class PredictionRequest(BaseModel):
    varsta: int = Field(..., ge=AGE_MIN, le=AGE_MAX)
    cesti_cafea_zi: int = Field(..., ge=COFFEE_CUPS_MIN, le=COFFEE_CUPS_MAX)
    ore_somn: float = Field(..., ge=SLEEP_HOURS_MIN, le=SLEEP_HOURS_MAX)
    nivel_stres: int = Field(..., ge=1, le=10)

class FormSubmissionResponse(BaseModel):
    score: float
    message: str
    submission_id: int

class PredictionResponse(BaseModel):
    predictie_stres: float
    submission_id: int
