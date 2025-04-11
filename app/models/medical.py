import uuid
from enum import Enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Date, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

class PrescriptionStatusEnum(str, Enum):
    ACTIVE = "Active"
    COMPLETED = "Completed"
    DISCONTINUED = "Discontinued"

class Prescription(Base):
    __tablename__ = "prescriptions"
    
    prescription_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.doctor_id", ondelete="CASCADE"), nullable=False)
    medication_name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=False)
    instructions = Column(Text)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    status = Column(SQLEnum(PrescriptionStatusEnum), default=PrescriptionStatusEnum.ACTIVE)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="prescriptions")
    doctor = relationship("Doctor", back_populates="prescriptions")

class MedicalHistory(Base):
    __tablename__ = "medical_history"
    
    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    diagnosis = Column(Text, nullable=False)
    treatment = Column(Text)
    diagnosed_date = Column(Date, nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.doctor_id", ondelete="SET NULL"))
    additional_notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="medical_history")
    doctor = relationship("Doctor", back_populates="medical_histories")
