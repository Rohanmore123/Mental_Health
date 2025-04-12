import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

class Rating(Base):
    __tablename__ = "ratings"
    
    rating_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.doctor_id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)  # Rating from 1-5
    review = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient")
    doctor = relationship("Doctor")
