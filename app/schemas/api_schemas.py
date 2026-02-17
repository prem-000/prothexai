from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.database_models import UserRole

# Auth Schemas
class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole

    @field_validator("email")
    @classmethod
    def validate_gmail(cls, value: EmailStr):
        if not value.lower().endswith("@gmail.com"):
            raise ValueError("Only Gmail addresses are allowed")
        return value

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class Token(BaseModel):
    access_token: str
    token_type: str
    role: Optional[str] = None
    patient_id: Optional[str] = None

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str = "Unknown"
    role: UserRole
    created_at: datetime

# Patient Schemas
class PatientProfileCreate(BaseModel):
    name: str
    email: EmailStr
    age: int
    gender: str
    height_cm: Optional[float] = Field(None, ge=120, le=220)
    weight_kg: Optional[float] = Field(None, ge=30, le=200)
    blood_pressure_systolic: Optional[int] = Field(None, ge=80, le=200)
    blood_pressure_diastolic: Optional[int] = Field(None, ge=50, le=130)
    blood_sugar_mg_dl: Optional[int] = Field(None, ge=60, le=400)
    medical_conditions: Optional[List[str]] = []
    baseline_score: Optional[float] = 50.0
    amputation_level: Optional[str] = None
    device_type: Optional[str] = None

class PatientProfileOut(BaseModel):
    id: str
    user_id: str
    name: str = "Unknown"
    email: Optional[str] = None
    age: int = 0
    gender: str = "Unknown"
    height_cm: float = 0.0
    weight_kg: float = 0.0
    bmi: float = 0.0
    blood_pressure_systolic: Optional[int] = 0
    blood_pressure_diastolic: Optional[int] = 0
    blood_sugar_mg_dl: Optional[int] = 0
    amputation_level: Optional[str] = None
    device_type: Optional[str] = None
    medical_conditions: List[str] = []


class DailyInput(BaseModel):
    step_length_cm: float
    cadence_spm: float
    walking_speed_mps: float
    gait_symmetry_index: float
    skin_temperature_c: float
    skin_moisture: float
    pressure_distribution_index: float = Field(..., ge=0.0, le=1.0)
    daily_wear_hours: float = 8.0

class GaitUploadResponse(BaseModel):
    message: str
    record_id: str

# Analysis Schemas
class AnalysisOut(BaseModel):
    record_id: str
    gait_abnormality: str
    skin_risk: str
    prosthetic_health_score: float
    recommendations: List[str]

# Dashboard Schemas
class TrendData(BaseModel):
    health_score: List[float] = []
    symmetry: List[float] = []
    walking_speed: List[float] = []
    skin_temp: List[float] = []
    moisture: List[float] = []
    pressure_distribution: List[float] = []

class DashboardSummary(BaseModel):
    patient_name: str
    latest_health_score: Optional[float] = None
    gait_abnormality: str = "Normal"
    skin_risk: str = "Low"
    trends: TrendData
    recent_alerts: List[str] = []

# Feedback Schemas
class FeedbackCreate(BaseModel):
    issue_type: str
    description: str

class FeedbackUpdate(BaseModel):
    status: str
    admin_response: str

class FeedbackOut(BaseModel):
    id: str
    patient_id: str
    patient_name: Optional[str] = "Unknown"
    issue_type: str
    description: str
    status: str
    admin_response: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class AdminDashboardSummary(BaseModel):
    total_patients: int
    total_feedback: int
    open_issues: int
    resolved_issues: int
    risk_distribution: Dict[str, int]
