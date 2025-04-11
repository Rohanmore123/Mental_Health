from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.users import User, Patient
from app.schemas.communication import MoodAnalysisRequest, MoodAnalysisResponse
from app.services.auth import get_current_active_user, check_user_role
from app.services.analytics import AnalyticsService

router = APIRouter()

@router.post("/mood", response_model=MoodAnalysisResponse)
def analyze_mood(
    request: MoodAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Analyze patient mood based on diary entries and chat messages.
    """
    # Check if user is the patient or a doctor/admin
    try:
        # Use direct database access to avoid SQLAlchemy issues
        import psycopg2
        from urllib.parse import unquote
        from app.config import settings

        # Parse the connection string
        db_url = settings.DATABASE_URL
        parts = db_url.split("://")[1].split("@")
        user_pass = parts[0].split(":")
        host_port_db = parts[1].split("/")
        host_port = host_port_db[0].split(":")

        username = user_pass[0]
        password = unquote(user_pass[1]) if "%" in user_pass[1] else user_pass[1]
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else "5432"
        database = host_port_db[1]

        # Connect to the database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )

        # Create a cursor
        cur = conn.cursor()

        # Check if user is the patient
        cur.execute(
            "SELECT * FROM patients WHERE user_id = %s AND patient_id = %s",
            (str(current_user.user_id), str(request.patient_id))
        )
        is_patient = cur.fetchone() is not None

        # Close the connection
        conn.close()

        # Check if user has doctor or admin role
        roles = current_user.roles.split(",") if current_user.roles else []
        is_doctor = "doctor" in roles
        is_admin = "admin" in roles

        is_authorized = is_patient or is_doctor or is_admin

        if not is_authorized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions. You must be the patient, a doctor, or an admin to access this resource."
            )
    except Exception as e:
        print(f"Error checking permissions: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking permissions: {str(e)}"
        )

    # Check if patient exists
    patient = db.query(Patient).filter(Patient.patient_id == request.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    # Analyze mood
    result = AnalyticsService.analyze_mood(db, request)

    return MoodAnalysisResponse(
        patient_id=result["patient_id"],
        mood_scores=result["mood_scores"],
        trend=result["trend"],
        recommendations=result["recommendations"]
    )
