from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

# Base schema
class RatingBase(BaseModel):
    patient_id: UUID
    doctor_id: UUID
    rating: int = Field(..., ge=1, le=5)  # Rating from 1-5
    review: Optional[str] = None

# Create schema
class RatingCreate(RatingBase):
    pass

# Update schema
class RatingUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    review: Optional[str] = None

# Response schema
class RatingResponse(RatingBase):
    rating_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
