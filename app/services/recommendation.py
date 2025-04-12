from datetime import datetime, date, time
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload

from app.models.users import Doctor, Patient, User
from app.models.communication import ChatMessage
from app.models.ratings import Rating
from app.models.appointments import Appointment, AppointmentStatusEnum

def score_doctor(doctor, patient, past_messages, db):
    """
    Score a doctor based on matching criteria with a patient.

    Args:
        doctor: Doctor object
        patient: Patient object
        past_messages: List of chat messages from the patient
        db: Database session

    Returns:
        Numeric score representing match quality
    """
    score = 0

    # Basic matching criteria
    if doctor.language == patient.language:
        score += 5
    if doctor.religion == patient.religion:
        score += 2
    # Note: region is not a field in the Doctor model, using address as a proxy
    if doctor.address and patient.address and doctor.address.lower() == patient.address.lower():
        score += 4

    # Chat Message Matching
    common_keywords = ["stress", "depression", "anxiety", "relationship", "trauma", "insomnia"]
    for message in past_messages:
        for keyword in common_keywords:
            if keyword in message.message_text.lower() and keyword in doctor.specialization.lower():
                score += 5

    # Rating Score
    ratings = db.query(Rating).filter(Rating.doctor_id == doctor.doctor_id).all()
    if ratings:
        avg_rating = sum(r.rating for r in ratings) / len(ratings)
        score += avg_rating

    return round(score, 2)

def get_doctor_recommendations(patient_id: str, db: Session, filters: dict = None):
    """
    Get doctor recommendations for a patient with optional filters.

    Args:
        patient_id: UUID of the patient
        db: Database session
        filters: Dictionary of filter criteria

    Returns:
        List of recommended doctors with scores
    """
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        return {"error": "Patient not found"}

    past_messages = db.query(ChatMessage).filter(ChatMessage.sender_id == patient_id).all()

    # Step 1: Filtered Doctors
    filtered_query = db.query(Doctor).options(
        joinedload(Doctor.availability),
        joinedload(Doctor.user)
    )

    # Join with User to ensure we only get active doctors
    filtered_query = filtered_query.join(User, Doctor.user_id == User.user_id).filter(User.is_active == True)

    if filters:
        # Language filter
        if "language" in filters and filters["language"]:
            filtered_query = filtered_query.filter(Doctor.language == filters["language"])

        # Address/Region filter
        if "region" in filters and filters["region"]:
            filtered_query = filtered_query.filter(Doctor.address.ilike(f"%{filters['region']}%"))

        # Gender filter
        if "gender" in filters and filters["gender"]:
            filtered_query = filtered_query.filter(Doctor.gender == filters["gender"])

        # Specialization filter
        if "specialization" in filters and filters["specialization"]:
            filtered_query = filtered_query.filter(
                Doctor.specialization.ilike(f"%{filters['specialization']}%")
            )

        # Availability filter
        if "availability" in filters and filters["availability"]:
            availability = filters["availability"]

            # Day of week filter
            if "day" in availability and availability["day"]:
                day = availability["day"]
                filtered_query = filtered_query.filter(
                    Doctor.availability.any(day_of_week=day)
                )

            # Time range filter
            if "start_time" in availability and "end_time" in availability:
                start_time = availability["start_time"]
                end_time = availability["end_time"]

                if start_time and end_time:
                    # Find doctors available during this time range
                    filtered_query = filtered_query.filter(
                        Doctor.availability.any(
                            and_(
                                func.cast(Doctor.availability.start_time, time) <= start_time,
                                func.cast(Doctor.availability.end_time, time) >= end_time
                            )
                        )
                    )

            # Check for existing appointments to exclude busy doctors
            if "date" in availability and availability["date"]:
                appointment_date = availability["date"]

                if "start_time" in availability and availability["start_time"]:
                    appointment_time = availability["start_time"]

                    # Exclude doctors with conflicting appointments
                    busy_doctors = db.query(Appointment.doctor_id).filter(
                        Appointment.appointment_date == appointment_date,
                        Appointment.appointment_time == appointment_time,
                        Appointment.status != AppointmentStatusEnum.CANCELLED
                    ).all()

                    busy_doctor_ids = [doc.doctor_id for doc in busy_doctors]
                    if busy_doctor_ids:
                        filtered_query = filtered_query.filter(
                            Doctor.doctor_id.notin_(busy_doctor_ids)
                        )

    filtered_doctors = filtered_query.all()
    filtered_scores = []

    for doctor in filtered_doctors:
        score = score_doctor(doctor, patient, past_messages, db)
        filtered_scores.append((doctor, score))

    # Step 2: Rule-based Completion (if < 5 doctors found)
    if len(filtered_scores) < 5:
        filtered_ids = [doc.doctor_id for doc, _ in filtered_scores]
        remaining_doctors = db.query(Doctor).options(
            joinedload(Doctor.availability),
            joinedload(Doctor.user)
        ).filter(
            Doctor.doctor_id.notin_(filtered_ids),
            Doctor.user.has(is_active=True)
        ).all()

        remaining_scores = []

        for doctor in remaining_doctors:
            score = score_doctor(doctor, patient, past_messages, db)
            remaining_scores.append((doctor, score))

        # Sort and pick top remaining doctors to fill the gap
        remaining_scores.sort(key=lambda x: x[1], reverse=True)
        doctors_needed = 5 - len(filtered_scores)
        filtered_scores += remaining_scores[:doctors_needed]

    # Final Deduplication & Packaging
    unique_doctors = {}
    for doctor, score in filtered_scores:
        if doctor.doctor_id not in unique_doctors:
            user = doctor.user

            # Get ratings
            ratings = db.query(Rating).filter(Rating.doctor_id == doctor.doctor_id).all()
            avg_rating = round(sum(r.rating for r in ratings) / len(ratings), 2) if ratings else "N/A"

            # Get availability
            availability = []
            for avail in doctor.availability:
                availability.append({
                    "day": avail.day_of_week,
                    "start_time": avail.start_time.strftime("%H:%M"),
                    "end_time": avail.end_time.strftime("%H:%M")
                })

            # Format doctor info
            full_name = f"{user.first_name} {user.last_name}" if user else "N/A"
            gender = user.gender.value if user and user.gender else "N/A"

            unique_doctors[doctor.doctor_id] = {
                "doctor_id": doctor.doctor_id,
                "name": full_name,
                "gender": gender,
                "specialization": doctor.specialization,
                "language": doctor.language,
                "address": doctor.address,
                "average_rating": avg_rating,
                "consultation_fee": float(doctor.consultation_fee),
                "availability": availability,
                "score": score,
            }

    # Sort so filtered doctors (who were added first) stay on top
    final_recommendations = list(unique_doctors.values())
    final_recommendations.sort(key=lambda x: x["score"], reverse=True)
    return final_recommendations[:5]
