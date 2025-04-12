from typing import Any, List, Dict, Optional
from uuid import UUID
from datetime import datetime, time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.users import User
from app.services.auth import get_current_active_user
from app.services.recommendation import get_doctor_recommendations

router = APIRouter()

class AvailabilityFilter(BaseModel):
    day: Optional[str] = None
    date: Optional[datetime] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None

class DoctorFilter(BaseModel):
    language: Optional[str] = None
    region: Optional[str] = None
    gender: Optional[str] = None
    specialization: Optional[str] = None
    availability: Optional[AvailabilityFilter] = None

class DoctorRecommendationRequest(BaseModel):
    patient_id: UUID
    filters: Optional[DoctorFilter] = None

@router.post("/doctors", response_model=List[Dict[str, Any]])
def recommend_doctors(
    request: DoctorRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get doctor recommendations for a patient with optional filters.
    """
    try:
        # Convert filters to dict if provided
        filters = None
        if request.filters:
            filters = request.filters.dict(exclude_none=True)
        
        # Get recommendations
        recommendations = get_doctor_recommendations(
            patient_id=str(request.patient_id),
            db=db,
            filters=filters
        )
        
        if isinstance(recommendations, dict) and "error" in recommendations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=recommendations["error"]
            )
            
        return recommendations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting doctor recommendations: {str(e)}"
        )
