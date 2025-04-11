from datetime import date, datetime, time, timedelta
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base
from app.models.users import User, Patient, Doctor, DoctorAvailability, Role, UserRole, GenderEnum
from app.models.appointments import Appointment, AppointmentStatus, AppointmentStatusEnum
from app.utils.security import get_password_hash

def seed_db():
    """Seed the database with initial data."""
    print("Seeding database with initial data...")
    
    # Create a synchronous engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Create a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create roles
        roles = [
            Role(role_id=uuid.uuid4(), role_name="admin"),
            Role(role_id=uuid.uuid4(), role_name="doctor"),
            Role(role_id=uuid.uuid4(), role_name="patient")
        ]
        db.add_all(roles)
        db.commit()
        
        # Create admin user
        admin_user = User(
            user_id=uuid.uuid4(),
            title="Mr.",
            first_name="Admin",
            last_name="User",
            gender=GenderEnum.MALE,
            email="admin@prasha.com",
            password_hash=get_password_hash("admin123"),
            roles="admin",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        
        # Create doctor user
        doctor_user = User(
            user_id=uuid.uuid4(),
            title="Dr.",
            first_name="John",
            last_name="Smith",
            gender=GenderEnum.MALE,
            email="doctor@prasha.com",
            password_hash=get_password_hash("doctor123"),
            roles="doctor",
            is_active=True
        )
        db.add(doctor_user)
        db.commit()
        
        # Create doctor profile
        doctor = Doctor(
            doctor_id=uuid.uuid4(),
            user_id=doctor_user.user_id,
            title="Dr.",
            first_name="John",
            middle_name="",
            last_name="Smith",
            dob=date(1980, 1, 15),
            gender=GenderEnum.MALE,
            language="English",
            religion="",
            address="123 Medical Center, New York",
            phone="555-123-4567",
            email="doctor@prasha.com",
            specialization="Cardiology",
            consultation_fee=150.00,
            treatment="General cardiology consultation",
            health_score=95
        )
        db.add(doctor)
        db.commit()
        
        # Create doctor availability
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        for day in days_of_week:
            availability = DoctorAvailability(
                availability_id=uuid.uuid4(),
                doctor_id=doctor.doctor_id,
                day_of_week=day,
                start_time=datetime.combine(date.today(), time(9, 0)),
                end_time=datetime.combine(date.today(), time(17, 0))
            )
            db.add(availability)
        db.commit()
        
        # Create patient user
        patient_user = User(
            user_id=uuid.uuid4(),
            title="Ms.",
            first_name="Jane",
            last_name="Doe",
            gender=GenderEnum.FEMALE,
            email="patient@prasha.com",
            password_hash=get_password_hash("patient123"),
            roles="patient",
            is_active=True
        )
        db.add(patient_user)
        db.commit()
        
        # Create patient profile
        patient = Patient(
            patient_id=uuid.uuid4(),
            user_id=patient_user.user_id,
            title="Ms.",
            first_name="Jane",
            middle_name="",
            last_name="Doe",
            dob=date(1990, 5, 20),
            gender=GenderEnum.FEMALE,
            language="English",
            religion="",
            address="456 Residential St, New York",
            phone="555-987-6543",
            email="patient@prasha.com",
            interests="Yoga, Meditation",
            treatment="Regular check-up",
            health_score=85
        )
        db.add(patient)
        db.commit()
        
        # Create appointment
        appointment = Appointment(
            appointment_id=uuid.uuid4(),
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            appointment_date=date.today() + timedelta(days=3),
            appointment_time=time(10, 30),
            visit_reason="Regular heart check-up",
            consultation_type="In-person",
            status=AppointmentStatusEnum.SCHEDULED
        )
        db.add(appointment)
        db.commit()
        
        # Create appointment status options
        status_options = [
            AppointmentStatus(status_code="Scheduled", description="Appointment is scheduled"),
            AppointmentStatus(status_code="Completed", description="Appointment has been completed"),
            AppointmentStatus(status_code="Cancelled", description="Appointment has been cancelled")
        ]
        db.add_all(status_options)
        db.commit()
        
        print("Database seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
