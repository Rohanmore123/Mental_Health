import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Boolean, DateTime, Date, Integer, ForeignKey, Numeric, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

class GenderEnum(str, Enum):
    M = "M"
    F = "F"
    Other = "Other"

class User(Base):
    __tablename__ = "users"

    user_id = Column("user_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column("title", String(50))
    first_name = Column("first_name", String(100), nullable=False)
    middle_name = Column("middle_name", String(100))
    last_name = Column("last_name", String(100), nullable=False)
    gender = Column("gender", SQLEnum(GenderEnum))
    email = Column("email", String(255), unique=True, nullable=False)
    password_hash = Column("password_hash", Text, nullable=False)
    roles = Column("roles", String(100), nullable=False)
    profile_picture = Column("profile_picture", Text)
    is_active = Column("is_active", Boolean, default=True)
    last_login = Column("last_login", DateTime)
    is_deleted = Column("is_deleted", Boolean, default=False)
    created_at = Column("created_at", DateTime, default=func.now())
    updated_at = Column("updated_at", DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="user", uselist=False, cascade="all, delete-orphan")
    doctor = relationship("Doctor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")

class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column("patient_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column("user_id", UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    title = Column("title", String(50))
    first_name = Column("first_name", String(100), nullable=False)
    middle_name = Column("middle_name", String(100))
    last_name = Column("last_name", String(100), nullable=False)
    dob = Column("dob", Date, nullable=False)
    gender = Column("gender", SQLEnum(GenderEnum), nullable=False)
    language = Column("language", String(50))
    religion = Column("religion", String(50))
    address = Column("address", Text)
    phone = Column("phone", String(15), unique=True)
    email = Column("email", String(255), unique=True)
    interests = Column("interests", Text)
    treatment = Column("treatment", Text, nullable=False)
    health_score = Column("health_score", Integer)
    under_medications = Column("under_medications", Boolean, default=False)
    created_at = Column("created_at", DateTime, default=func.now())
    updated_at = Column("updated_at", DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="patient", cascade="all, delete-orphan")
    medical_history = relationship("MedicalHistory", back_populates="patient", cascade="all, delete-orphan")
    diaries = relationship("Mydiary", back_populates="patient", cascade="all, delete-orphan")
    timelines = relationship("MyTimeline", back_populates="patient", cascade="all, delete-orphan")
    timeline_events = relationship("MyTimelineEvent", back_populates="patient", cascade="all, delete-orphan")

class Doctor(Base):
    __tablename__ = "doctors"

    doctor_id = Column("doctor_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column("user_id", UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    title = Column("title", String(50))
    first_name = Column("first_name", String(100), nullable=False)
    middle_name = Column("middle_name", String(100))
    last_name = Column("last_name", String(100), nullable=False)
    dob = Column("dob", Date, nullable=False)
    gender = Column("gender", SQLEnum(GenderEnum), nullable=False)
    language = Column("language", String(50))
    religion = Column("religion", String(50))
    address = Column("address", Text)
    phone = Column("phone", String(15), unique=True)
    email = Column("email", String(255), unique=True)
    interests = Column("interests", Text)
    specialization = Column("specialization", Text)
    consultation_fee = Column("consultation_fee", Numeric(10, 2), nullable=False)
    treatment = Column("treatment", Text, nullable=False)
    health_score = Column("health_score", Integer)
    under_medications = Column("under_medications", Boolean, default=False)
    created_at = Column("created_at", DateTime, default=func.now())
    updated_at = Column("updated_at", DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="doctor")
    availability = relationship("DoctorAvailability", back_populates="doctor", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="doctor", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="doctor", cascade="all, delete-orphan")
    medical_histories = relationship("MedicalHistory", back_populates="doctor", cascade="all, delete-orphan")

class DoctorAvailability(Base):
    __tablename__ = "doctors_availability"

    availability_id = Column("availability_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column("doctor_id", UUID(as_uuid=True), ForeignKey("doctors.doctor_id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column("day_of_week", String(20), nullable=False)
    start_time = Column("start_time", DateTime, nullable=False)
    end_time = Column("end_time", DateTime, nullable=False)

    # Relationships
    doctor = relationship("Doctor", back_populates="availability")

class Role(Base):
    __tablename__ = "roles"

    role_id = Column("role_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_name = Column("role_name", String(100), unique=True, nullable=False)

    # Relationships
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column("user_id", UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    role_id = Column("role_id", UUID(as_uuid=True), ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
