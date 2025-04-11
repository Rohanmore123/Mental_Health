from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.users import User
from app.schemas.users import UserResponse
from app.services.auth import get_current_active_user

router = APIRouter()

@router.get("/me", response_model=dict)
def read_current_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get current user.
    """
    try:
        # Use raw SQL to get user data
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
        
        # Get user data
        cur.execute(
            "SELECT * FROM users WHERE user_id = %s",
            (str(current_user.user_id),)
        )
        user = cur.fetchone()
        
        if not user:
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get column names
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'users'
            ORDER BY ordinal_position
        """)
        columns = [col[0] for col in cur.fetchall()]
        
        # Create user dict
        user_dict = dict(zip(columns, user))
        
        # Remove sensitive data
        if 'password_hash' in user_dict:
            del user_dict['password_hash']
        
        # Check if user has a patient record
        cur.execute(
            "SELECT * FROM patients WHERE user_id = %s",
            (str(user_dict['user_id']),)
        )
        patient = cur.fetchone()
        
        if patient:
            # Get column names
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'patients'
                ORDER BY ordinal_position
            """)
            patient_columns = [col[0] for col in cur.fetchall()]
            
            # Create patient dict
            patient_dict = dict(zip(patient_columns, patient))
            
            # Add patient data to user dict
            user_dict['patient_id'] = patient_dict['patient_id']
            user_dict['health_score'] = patient_dict['health_score']
        
        # Check if user has a doctor record
        cur.execute(
            "SELECT * FROM doctors WHERE user_id = %s",
            (str(user_dict['user_id']),)
        )
        doctor = cur.fetchone()
        
        if doctor:
            # Get column names
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'doctors'
                ORDER BY ordinal_position
            """)
            doctor_columns = [col[0] for col in cur.fetchall()]
            
            # Create doctor dict
            doctor_dict = dict(zip(doctor_columns, doctor))
            
            # Add doctor data to user dict
            user_dict['doctor_id'] = doctor_dict['doctor_id']
            user_dict['specialization'] = doctor_dict['specialization']
            user_dict['consultation_fee'] = float(doctor_dict['consultation_fee']) if doctor_dict['consultation_fee'] else None
        
        # Close the connection
        conn.close()
        
        return user_dict
    
    except Exception as e:
        print(f"Error getting user profile: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
