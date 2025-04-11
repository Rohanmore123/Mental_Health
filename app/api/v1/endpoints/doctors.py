from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.users import Doctor, DoctorAvailability, User
from app.schemas.users import (
    DoctorCreate, DoctorResponse, DoctorUpdate,
    DoctorAvailabilityCreate, DoctorAvailabilityResponse, DoctorAvailabilityUpdate,
    DoctorRecommendationRequest, DoctorRecommendationResponse
)
from app.services.auth import get_current_active_user, check_user_role
from app.services.doctor_recommendation import DoctorRecommendationService

router = APIRouter()

@router.get("/appointments", response_model=List[dict])
def get_doctor_appointments(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get doctor appointments.
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

        # Get doctor ID for the current user
        cur.execute(
            "SELECT doctor_id FROM doctors WHERE user_id = %s",
            (str(current_user.user_id),)
        )
        doctor_result = cur.fetchone()

        if not doctor_result:
            conn.close()
            return []

        doctor_id = doctor_result[0]

        # Get appointments for the doctor
        cur.execute(
            """
            SELECT a.*,
                   p.first_name as patient_first_name,
                   p.last_name as patient_last_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            WHERE a.doctor_id = %s
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
            """,
            (str(doctor_id),)
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

        # Add patient name columns
        appointment_columns.extend(['patient_first_name', 'patient_last_name'])

        # Create appointment dicts
        appointment_dicts = []
        for appointment in appointments:
            appointment_dict = dict(zip(appointment_columns, appointment))

            # Add patient name
            appointment_dict['patient_name'] = f"{appointment_dict['patient_first_name']} {appointment_dict['patient_last_name']}"

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
        print(f"Error getting doctor appointments: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/patients", response_model=List[dict])
def get_patients_list(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get list of patients for a doctor.
    """
    try:
        # Use raw SQL to get patients
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

        # Get doctor ID for the current user
        cur.execute(
            "SELECT doctor_id FROM doctors WHERE user_id = %s",
            (str(current_user.user_id),)
        )
        doctor_result = cur.fetchone()

        if not doctor_result:
            conn.close()
            return []

        doctor_id = doctor_result[0]

        # Get patients who have appointments with this doctor
        cur.execute(
            """
            SELECT DISTINCT p.*
            FROM patients p
            JOIN appointments a ON p.patient_id = a.patient_id
            WHERE a.doctor_id = %s
            ORDER BY p.last_name, p.first_name
            """,
            (str(doctor_id),)
        )
        patients = cur.fetchall()

        # Get column names
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'patients'
            ORDER BY ordinal_position
        """)
        patient_columns = [col[0] for col in cur.fetchall()]

        # Create patient dicts
        patient_dicts = []
        for patient in patients:
            patient_dict = dict(zip(patient_columns, patient))

            # Add full name
            patient_dict['full_name'] = f"{patient_dict['first_name']} {patient_dict['last_name']}"

            # Convert date to string
            if 'dob' in patient_dict and patient_dict['dob']:
                patient_dict['dob'] = patient_dict['dob'].isoformat()

            patient_dicts.append(patient_dict)

        # Close the connection
        conn.close()

        return patient_dicts

    except Exception as e:
        print(f"Error getting patients list: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/", response_model=DoctorResponse)
def create_doctor(
    doctor_in: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a new doctor.
    """
    # Check if user has admin role
    if not check_user_role(current_user, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Check if user_id is provided
    if not doctor_in.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID is required"
        )

    # Check if user exists
    user = db.query(User).filter(User.user_id == doctor_in.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if doctor already exists for this user
    doctor = db.query(Doctor).filter(Doctor.user_id == doctor_in.user_id).first()
    if doctor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor already exists for this user"
        )

    # Create new doctor
    db_doctor = Doctor(
        user_id=doctor_in.user_id,
        title=doctor_in.title,
        first_name=doctor_in.first_name,
        middle_name=doctor_in.middle_name,
        last_name=doctor_in.last_name,
        dob=doctor_in.dob,
        gender=doctor_in.gender,
        language=doctor_in.language,
        religion=doctor_in.religion,
        address=doctor_in.address,
        phone=doctor_in.phone,
        email=doctor_in.email,
        interests=doctor_in.interests,
        specialization=doctor_in.specialization,
        consultation_fee=doctor_in.consultation_fee,
        treatment=doctor_in.treatment,
        health_score=doctor_in.health_score,
        under_medications=doctor_in.under_medications
    )

    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)

    # Add availability if provided
    if doctor_in.availability:
        for availability in doctor_in.availability:
            db_availability = DoctorAvailability(
                doctor_id=db_doctor.doctor_id,
                day_of_week=availability.day_of_week,
                start_time=availability.start_time,
                end_time=availability.end_time
            )
            db.add(db_availability)

        db.commit()
        db.refresh(db_doctor)

    return db_doctor

@router.get("/", response_model=List[DoctorResponse])
def read_doctors(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve doctors.
    """
    doctors = db.query(Doctor).offset(skip).limit(limit).all()
    return doctors

@router.get("/{doctor_id}", response_model=DoctorResponse)
def read_doctor(
    doctor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get doctor by ID.
    """
    doctor = db.query(Doctor).filter(Doctor.doctor_id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    return doctor

@router.put("/{doctor_id}", response_model=DoctorResponse)
def update_doctor(
    doctor_id: UUID,
    doctor_in: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Update a doctor.
    """
    # Check if user has admin role or is the doctor being updated
    doctor = db.query(Doctor).filter(Doctor.doctor_id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )

    if not (check_user_role(current_user, "admin") or doctor.user_id == current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Update doctor fields
    for field, value in doctor_in.dict(exclude_unset=True).items():
        setattr(doctor, field, value)

    db.commit()
    db.refresh(doctor)

    return doctor

@router.delete("/{doctor_id}", response_model=DoctorResponse)
def delete_doctor(
    doctor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Delete a doctor.
    """
    # Check if user has admin role
    if not check_user_role(current_user, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    doctor = db.query(Doctor).filter(Doctor.doctor_id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )

    db.delete(doctor)
    db.commit()

    return doctor

@router.post("/availability", response_model=DoctorAvailabilityResponse)
def create_doctor_availability(
    availability_in: DoctorAvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a new doctor availability.
    """
    # Check if doctor exists
    doctor = db.query(Doctor).filter(Doctor.doctor_id == availability_in.doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )

    # Check if user has admin role or is the doctor
    if not (check_user_role(current_user, "admin") or doctor.user_id == current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Create new availability
    db_availability = DoctorAvailability(
        doctor_id=availability_in.doctor_id,
        day_of_week=availability_in.day_of_week,
        start_time=availability_in.start_time,
        end_time=availability_in.end_time
    )

    db.add(db_availability)
    db.commit()
    db.refresh(db_availability)

    return db_availability

@router.get("/test", response_model=dict)
def test_endpoint() -> Any:
    """
    Test endpoint to check if the API is working.
    """
    return {"status": "ok", "message": "Doctor API is working correctly"}

@router.post("/recommend", response_model=DoctorRecommendationResponse)
def recommend_doctors(
    request: DoctorRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Recommend doctors based on criteria.
    """
    # Check if user is a patient or a doctor/admin
    roles = current_user.roles.split(",") if current_user.roles else []
    is_patient = 'patient' in roles
    is_doctor = 'doctor' in roles
    is_admin = 'admin' in roles

    # Use direct database access to verify patient ID
    try:
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
        is_own_patient_id = cur.fetchone() is not None

        # Close the connection
        conn.close()

        # Check permissions
        if not (is_own_patient_id or is_doctor or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions. You can only request recommendations for your own patient ID."
            )
    except Exception as e:
        print(f"Error checking permissions: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking permissions: {str(e)}"
        )
    try:
        # Get recommended doctors
        recommended_doctors = DoctorRecommendationService.recommend_doctors(db, request)

        # Extract doctors and scores
        doctors = [item["doctor"] for item in recommended_doctors]

        # Get average score if there are recommendations
        avg_score = None
        if recommended_doctors:
            avg_score = sum(item["score"] for item in recommended_doctors) / len(recommended_doctors)

        return {
            "doctors": doctors,
            "recommendation_score": avg_score
        }
    except Exception as e:
        print(f"Error in doctor recommendations: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting doctor recommendations: {str(e)}"
        )
