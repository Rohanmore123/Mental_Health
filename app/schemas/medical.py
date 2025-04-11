from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

# Enums
class PrescriptionStatusEnum(str, Enum):
    ACTIVE = "Active"
    COMPLETED = "Completed"
    DISCONTINUED = "Discontinued"

# Base schemas
class PrescriptionBase(BaseModel):
    patient_id: UUID
    doctor_id: UUID
    medication_name: str
    dosage: str
    instructions: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None

# Create schemas
class PrescriptionCreate(PrescriptionBase):
    pass

# Update schemas
class PrescriptionUpdate(BaseModel):
    medication_name: Optional[str] = None
    dosage: Optional[str] = None
    instructions: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[PrescriptionStatusEnum] = None

# Response schemas
class PrescriptionResponse(PrescriptionBase):
    prescription_id: UUID
    status: PrescriptionStatusEnum
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Medical History schemas
class MedicalHistoryBase(BaseModel):
    patient_id: UUID
    diagnosis: str
    treatment: Optional[str] = None
    diagnosed_date: date
    doctor_id: Optional[UUID] = None
    additional_notes: Optional[str] = None

# Create schemas
class MedicalHistoryCreate(MedicalHistoryBase):
    pass

# Update schemas
class MedicalHistoryUpdate(BaseModel):
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    diagnosed_date: Optional[date] = None
    doctor_id: Optional[UUID] = None
    additional_notes: Optional[str] = None

# Response schemas
class MedicalHistoryResponse(MedicalHistoryBase):
    history_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
