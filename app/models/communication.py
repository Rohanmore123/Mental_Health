import uuid
from enum import Enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

class MessageTypeEnum(str, Enum):
    PATIENT = "P"
    DOCTOR = "D"
    AI = "AI"
    OTHER = "Other"

class NotificationTypeEnum(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

class NotificationStatusEnum(str, Enum):
    QUEUE = "in queue"
    SENT = "sent"
    VIEWED = "viewed"

class OtpStatusEnum(str, Enum):
    ACTIVE = "Active"
    VALIDATED = "Validated"
    RESENT = "Resent"

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    chat_message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(UUID(as_uuid=True))
    receiver_id = Column(UUID(as_uuid=True))
    message_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    attachment_url = Column(Text)
    extracted_keywords = Column(JSONB, nullable=True)

class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(UUID(as_uuid=True))
    receiver_id = Column(UUID(as_uuid=True))
    message_text = Column(Text, nullable=False)
    message_type = Column(String(50))  # email, sms/txt, push
    status = Column(String(50))  # in queue, sent, viewed
    scheduled_at = Column(DateTime)
    expiry_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    attachment_url = Column(Text)

class UserNotificationPreference(Base):
    __tablename__ = "user_notification_preferences"

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(UUID(as_uuid=True))
    receiver_id = Column(UUID(as_uuid=True))
    message_text = Column(Text, nullable=False)
    message_type = Column(String(50))  # email, sms/txt, push
    status = Column(String(50))  # in queue, sent, viewed
    scheduled_at = Column(DateTime)
    expiry_date = Column(DateTime)
    attachment_url = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())

class Otp(Base):
    __tablename__ = "otp"

    otp_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    otp_text = Column(String(100), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=func.now())
    valid_until = Column(DateTime)
    validated_at = Column(DateTime)
    status = Column(String(10), default="Active")  # Active, Validated, Resent

class Mydiary(Base):
    __tablename__ = "mydiary"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    notes = Column(Text, nullable=False)
    message_type = Column(SQLEnum(MessageTypeEnum), nullable=False, default=MessageTypeEnum.PATIENT)
    additional_notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="diaries")

class MyTimeline(Base):
    __tablename__ = "mytimeline"

    timeline_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    timeline_name = Column(String(200), nullable=False)
    timeline_description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="timelines")
    events = relationship("MyTimelineEvent", back_populates="timeline", cascade="all, delete-orphan")

class MyTimelineEvent(Base):
    __tablename__ = "mytimeline_events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timeline_id = Column(UUID(as_uuid=True), ForeignKey("mytimeline.timeline_id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)
    event_name = Column(String(100), nullable=False)
    event_description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    timeline = relationship("MyTimeline", back_populates="events")
    patient = relationship("Patient", back_populates="timeline_events")
