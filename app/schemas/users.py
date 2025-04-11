from datetime import date, datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

# Enums
class GenderEnum(str, Enum):
    MALE = "M"
    FEMALE = "F"
    OTHER = "Other"

# Base schemas
class UserBase(BaseModel):
    title: Optional[str] = None
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    gender: Optional[GenderEnum] = None
    email: EmailStr
    profile_picture: Optional[str] = None

class PatientBase(BaseModel):
    title: Optional[str] = None
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    dob: date
    gender: GenderEnum
    language: Optional[str] = None
    religion: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    interests: Optional[str] = None
    treatment: str
    health_score: Optional[int] = None
    under_medications: bool = False

class DoctorBase(BaseModel):
    title: Optional[str] = None
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    dob: date
    gender: GenderEnum
    language: Optional[str] = None
    religion: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    interests: Optional[str] = None
    specialization: Optional[str] = None
    consultation_fee: float
    treatment: str
    health_score: Optional[int] = None
    under_medications: bool = False

class DoctorAvailabilityBase(BaseModel):
    day_of_week: str
    start_time: datetime
    end_time: datetime

# Create schemas
class UserCreate(UserBase):
    password: str
    roles: str = "patient"  # Default role

class PatientCreate(PatientBase):
    user_id: Optional[UUID] = None

class DoctorCreate(DoctorBase):
    user_id: Optional[UUID] = None
    availability: Optional[List[DoctorAvailabilityBase]] = None

class DoctorAvailabilityCreate(DoctorAvailabilityBase):
    doctor_id: UUID

# Update schemas
class UserUpdate(BaseModel):
    title: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[GenderEnum] = None
    email: Optional[EmailStr] = None
    profile_picture: Optional[str] = None
    is_active: Optional[bool] = None

class PatientUpdate(BaseModel):
    title: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[GenderEnum] = None
    language: Optional[str] = None
    religion: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    interests: Optional[str] = None
    treatment: Optional[str] = None
    health_score: Optional[int] = None
    under_medications: Optional[bool] = None

class DoctorUpdate(BaseModel):
    title: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[GenderEnum] = None
    language: Optional[str] = None
    religion: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    interests: Optional[str] = None
    specialization: Optional[str] = None
    consultation_fee: Optional[float] = None
    treatment: Optional[str] = None
    health_score: Optional[int] = None
    under_medications: Optional[bool] = None

class DoctorAvailabilityUpdate(BaseModel):
    day_of_week: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

# Response schemas
class DoctorAvailabilityResponse(DoctorAvailabilityBase):
    availability_id: UUID
    doctor_id: UUID

    class Config:
        from_attributes = True

class UserResponse(UserBase):
    user_id: UUID
    roles: str
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PatientResponse(PatientBase):
    patient_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DoctorResponse(DoctorBase):
    doctor_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    availability: Optional[List[DoctorAvailabilityResponse]] = None

    class Config:
        from_attributes = True

# Doctor recommendation schemas
class DoctorRecommendationRequest(BaseModel):
    patient_id: UUID
    specialization: Optional[str] = None
    language: Optional[str] = None
    gender: Optional[GenderEnum] = None
    preferred_day: Optional[str] = None
    preferred_time: Optional[datetime] = None
    max_consultation_fee: Optional[float] = None

class DoctorRecommendationResponse(BaseModel):
    doctors: List[DoctorResponse]
    recommendation_score: Optional[float] = None
