from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.users import User
from app.services.auth import get_current_active_user

router = APIRouter()

@router.get("/test", response_model=dict)
def test_endpoint() -> Any:
    """
    Test endpoint to check if the API is working.
    """
    return {"status": "ok", "message": "Patient API is working correctly"}

@router.get("/appointments", response_model=List[dict])
def get_patient_appointments(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get patient appointments.
    """
    try:
        # Use raw SQL to get appointments
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

        # Get patient ID for the current user
        cur.execute(
            "SELECT patient_id FROM patients WHERE user_id = %s",
            (str(current_user.user_id),)
        )
        patient_result = cur.fetchone()

        if not patient_result:
            conn.close()
            return []

        patient_id = patient_result[0]

        # Get appointments for the patient
        cur.execute(
            """
            SELECT a.*,
                   d.first_name as doctor_first_name,
                   d.last_name as doctor_last_name
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.doctor_id
            WHERE a.patient_id = %s
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
            """,
            (str(patient_id),)
        )
        appointments = cur.fetchall()

        # Get column names
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'appointments'
            ORDER BY ordinal_position
        """)
        appointment_columns = [col[0] for col in cur.fetchall()]

        # Add doctor name columns
        appointment_columns.extend(['doctor_first_name', 'doctor_last_name'])

        # Create appointment dicts
        appointment_dicts = []
        for appointment in appointments:
            appointment_dict = dict(zip(appointment_columns, appointment))

            # Add doctor name
            appointment_dict['doctor_name'] = f"Dr. {appointment_dict['doctor_first_name']} {appointment_dict['doctor_last_name']}"

            # Convert date and time to strings
            if 'appointment_date' in appointment_dict:
                appointment_dict['appointment_date'] = appointment_dict['appointment_date'].isoformat()
            if 'appointment_time' in appointment_dict:
                appointment_dict['appointment_time'] = appointment_dict['appointment_time'].isoformat()

            appointment_dicts.append(appointment_dict)

        # Close the connection
        conn.close()

        return appointment_dicts

    except Exception as e:
        print(f"Error getting patient appointments: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
