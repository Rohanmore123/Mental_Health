from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.users import Doctor, DoctorAvailability
from app.schemas.users import GenderEnum, DoctorRecommendationRequest

class DoctorRecommendationService:
    """Service for doctor recommendations."""

    @staticmethod
    def recommend_doctors(
        db: Session, request: DoctorRecommendationRequest
    ) -> List[Dict[str, Any]]:
        """
        Recommend doctors based on various criteria.

        Args:
            db: Database session
            request: Doctor recommendation request

        Returns:
            List of recommended doctors with scores
        """
        # Start with a base query
        query = db.query(Doctor).options(
            joinedload(Doctor.availability)
        )

        # Join with User to check if the user is active
        query = query.join(Doctor.user).filter(
            Doctor.user.has(is_active=True)
        )

        # Apply filters based on request parameters
        if request.specialization:
            query = query.filter(
                func.lower(Doctor.specialization).contains(request.specialization.lower())
            )

        if request.language:
            query = query.filter(
                func.lower(Doctor.language) == request.language.lower()
            )

        if request.gender:
            query = query.filter(Doctor.gender == request.gender)

        if request.max_consultation_fee:
            query = query.filter(Doctor.consultation_fee <= request.max_consultation_fee)

        # Get all matching doctors
        doctors = query.all()

        # Calculate recommendation scores
        recommended_doctors = []
        for doctor in doctors:
            score = DoctorRecommendationService._calculate_recommendation_score(
                doctor, request
            )

            recommended_doctors.append({
                "doctor": doctor,
                "score": score
            })

        # Sort by score (descending)
        recommended_doctors.sort(key=lambda x: x["score"], reverse=True)

        return recommended_doctors

    @staticmethod
    def _calculate_recommendation_score(
        doctor: Doctor, request: DoctorRecommendationRequest
    ) -> float:
        """
        Calculate a recommendation score for a doctor based on the request.

        Args:
            doctor: Doctor object
            request: Doctor recommendation request

        Returns:
            Recommendation score (0-100)
        """
        score = 50.0  # Base score

        # Specialization match (highest weight)
        if request.specialization and doctor.specialization:
            if request.specialization.lower() in doctor.specialization.lower():
                score += 25.0

        # Language match
        if request.language and doctor.language:
            if request.language.lower() == doctor.language.lower():
                score += 10.0

        # Gender match
        if request.gender and doctor.gender:
            if request.gender == doctor.gender:
                score += 5.0

        # Availability match
        if request.preferred_day and doctor.availability:
            for availability in doctor.availability:
                if request.preferred_day.lower() == availability.day_of_week.lower():
                    score += 5.0

                    # Preferred time match
                    if request.preferred_time:
                        preferred_time = request.preferred_time.time()
                        if (availability.start_time.time() <= preferred_time <=
                            availability.end_time.time()):
                            score += 5.0

                    break

        # Fee match
        if request.max_consultation_fee:
            if doctor.consultation_fee <= request.max_consultation_fee:
                # The lower the fee compared to max, the higher the score
                fee_ratio = 1 - (doctor.consultation_fee / request.max_consultation_fee)
                score += fee_ratio * 10.0

        # Ensure score is within 0-100 range
        return max(0, min(100, score))
