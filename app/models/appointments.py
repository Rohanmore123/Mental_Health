import uuid
from enum import Enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Date, Time, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

class AppointmentStatusEnum(str, Enum):
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class Appointment(Base):
    __tablename__ = "appointments"
    
    appointment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.doctor_id", ondelete="CASCADE"), nullable=False)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Time, nullable=False)
    visit_reason = Column(Text)
    consultation_type = Column(String(50))
    status = Column(SQLEnum(AppointmentStatusEnum), default=AppointmentStatusEnum.SCHEDULED)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")

class AppointmentStatus(Base):
    __tablename__ = "appointment_status"
    
    status_code = Column(String(20), primary_key=True)
    description = Column(Text)
