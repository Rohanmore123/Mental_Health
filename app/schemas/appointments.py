from datetime import date, datetime, time
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

# Enums
class AppointmentStatusEnum(str, Enum):
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

# Base schemas
class AppointmentBase(BaseModel):
    patient_id: UUID
    doctor_id: UUID
    appointment_date: date
    appointment_time: time
    visit_reason: Optional[str] = None
    consultation_type: Optional[str] = None
    notes: Optional[str] = None

# Create schemas
class AppointmentCreate(AppointmentBase):
    pass

# Update schemas
class AppointmentUpdate(BaseModel):
    appointment_date: Optional[date] = None
    appointment_time: Optional[time] = None
    visit_reason: Optional[str] = None
    consultation_type: Optional[str] = None
    status: Optional[AppointmentStatusEnum] = None
    notes: Optional[str] = None

# Response schemas
class AppointmentResponse(AppointmentBase):
    appointment_id: UUID
    status: AppointmentStatusEnum
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
