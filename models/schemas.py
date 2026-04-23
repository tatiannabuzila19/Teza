from pydantic import BaseModel, Field, validator
from typing import Optional
from enum import Enum
from config import AGE_MIN, AGE_MAX, COFFEE_CUPS_MIN, COFFEE_CUPS_MAX, SLEEP_HOURS_MIN, SLEEP_HOURS_MAX, HEIGHT_MIN, HEIGHT_MAX, WEIGHT_MIN, WEIGHT_MAX, HEART_RATE_MIN, HEART_RATE_MAX, ACTIVITY_MIN, ACTIVITY_MAX

class Gender(str, Enum):
    MASCULINE = "Masculin"
    FEMININE = "Feminin"
    OTHER = "Altul"

class Country(str, Enum):
    ROMANIA = "România"
    AUSTRIA = "Austria"
    BELGIUM = "Belgia"
    BULGARIA = "Bulgaria"
    CROATIA = "Croația"
    CYPRUS = "Cipru"
    CZECH = "Cehia"
    DENMARK = "Danemarca"
    ESTONIA = "Estonia"
    FINLAND = "Finlanda"
    FRANCE = "Franța"
    GERMANY = "Germania"
    GREECE = "Grecia"
    HUNGARY = "Ungaria"
    IRELAND = "Irlanda"
    ITALY = "Italia"
    LATVIA = "Letonia"
    LITHUANIA = "Lituania"
    LUXEMBOURG = "Luxemburg"
    MALTA = "Malta"
    NETHERLANDS = "Olanda"
    POLAND = "Polonia"
    PORTUGAL = "Portugalia"
    SLOVAKIA = "Slovacia"
    SLOVENIA = "Slovenia"
    SPAIN = "Spania"
    SWEDEN = "Suedia"

class Occupation(str, Enum):
    STUDENT = "Student"
    OFFICE = "Birou"
    HEALTHCARE = "Sănătate"
    SERVICES = "Servicii"
    OTHER = "Altul"

class SleepQuality(str, Enum):
    EXCELLENT = "Excelent"
    GOOD = "Bun"
    MEDIUM = "Mediu"
    POOR = "Slab"

class HealthIssues(str, Enum):
    NONE = "Niciunul"
    MILD = "Ușoare"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class BooleanChoice(str, Enum):
    YES = "Da"
    NO = "Nu"

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

# Form submission - NEW MODEL with 14 features
class FormSubmissionRequest(BaseModel):
    # Block 1: Coffee & Sleep
    coffee_cups: int = Field(..., ge=COFFEE_CUPS_MIN, le=COFFEE_CUPS_MAX)
    sleep_hours: float = Field(..., ge=SLEEP_HOURS_MIN, le=SLEEP_HOURS_MAX)
    sleep_quality: SleepQuality
    
    # Block 2: Activity & Body
    activity_hours: float = Field(..., ge=ACTIVITY_MIN, le=ACTIVITY_MAX)
    height_cm: int = Field(..., ge=HEIGHT_MIN, le=HEIGHT_MAX, description="Height in cm")
    weight_kg: float = Field(..., ge=WEIGHT_MIN, le=WEIGHT_MAX, description="Weight in kg")
    heart_rate: int = Field(..., ge=HEART_RATE_MIN, le=HEART_RATE_MAX, description="Resting heart rate in bpm")
    
    # Block 3: Personal Data
    age: int = Field(..., ge=AGE_MIN, le=AGE_MAX)
    gender: Gender
    country: Country
    occupation: Occupation
    
    # Block 4: Lifestyle
    smoking: BooleanChoice
    alcohol: BooleanChoice
    country: str = "Romania"  # Default value, not user-selected
    health_issues: HealthIssues

class FormSubmissionResponse(BaseModel):
    prediction: float  # ML model prediction (stress level 0-10)
    prediction_category: str  # Low/Medium/High
    message: str
    submission_id: int
    details: dict  # Additional info like BMI

class PredictionRequest(BaseModel):
    varsta: int = Field(..., ge=AGE_MIN, le=AGE_MAX)
    cesti_cafea_zi: int = Field(..., ge=COFFEE_CUPS_MIN, le=COFFEE_CUPS_MAX)
    ore_somn: float = Field(..., ge=SLEEP_HOURS_MIN, le=SLEEP_HOURS_MAX)
    nivel_stres: int = Field(..., ge=1, le=10)

class PredictionResponse(BaseModel):
    predictie_stres: float
    submission_id: int
