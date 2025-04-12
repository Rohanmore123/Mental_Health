from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel

# Enums
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

# Chat schemas
class ChatMessageBase(BaseModel):
    sender_id: UUID
    receiver_id: Optional[UUID] = None
    message_text: str
    attachment_url: Optional[str] = None

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessageResponse(ChatMessageBase):
    chat_message_id: UUID
    timestamp: datetime

    class Config:
        from_attributes = True

# AI Chat schemas
class AIChatRequest(BaseModel):
    user_id: UUID
    message: str
    audio_file: Optional[str] = None  # Base64 encoded audio or file path

class AIChatResponse(BaseModel):
    response: str
    audio_response: Optional[str] = None  # Base64 encoded audio
    sentiment_analysis: Optional[Dict[str, Any]] = None
    extracted_keywords: Optional[List[str]] = None

# Notification schemas
class NotificationBase(BaseModel):
    sender_id: Optional[UUID] = None
    receiver_id: UUID
    message_text: str
    message_type: NotificationTypeEnum
    scheduled_at: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    attachment_url: Optional[str] = None

class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    notification_id: UUID
    status: NotificationStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True

# User Notification Preferences
class UserNotificationPreferenceBase(BaseModel):
    user_id: UUID
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True

class UserNotificationPreferenceCreate(UserNotificationPreferenceBase):
    pass

class UserNotificationPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None

class UserNotificationPreferenceResponse(UserNotificationPreferenceBase):
    class Config:
        from_attributes = True

# Diary schemas
class DiaryEntryBase(BaseModel):
    patient_id: UUID
    notes: str
    message_type: MessageTypeEnum = MessageTypeEnum.PATIENT
    additional_notes: Optional[str] = None

class DiaryEntryCreate(DiaryEntryBase):
    pass

class DiaryEntryUpdate(BaseModel):
    notes: Optional[str] = None
    message_type: Optional[MessageTypeEnum] = None
    additional_notes: Optional[str] = None

class DiaryEntryResponse(DiaryEntryBase):
    event_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Timeline schemas
class TimelineBase(BaseModel):
    patient_id: UUID
    timeline_name: str
    timeline_description: Optional[str] = None

class TimelineCreate(TimelineBase):
    pass

class TimelineUpdate(BaseModel):
    timeline_name: Optional[str] = None
    timeline_description: Optional[str] = None

class TimelineEventBase(BaseModel):
    timeline_id: UUID
    patient_id: UUID
    event_type: str
    event_name: str
    event_description: Optional[str] = None

class TimelineEventCreate(TimelineEventBase):
    pass

class TimelineEventUpdate(BaseModel):
    event_type: Optional[str] = None
    event_name: Optional[str] = None
    event_description: Optional[str] = None

class TimelineEventResponse(TimelineEventBase):
    event_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TimelineResponse(TimelineBase):
    timeline_id: UUID
    created_at: datetime
    updated_at: datetime
    events: Optional[List[TimelineEventResponse]] = None

    class Config:
        from_attributes = True

# Analytics schemas
class MoodAnalysisRequest(BaseModel):
    patient_id: UUID
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class MoodAnalysisResponse(BaseModel):
    patient_id: UUID
    mood_scores: Dict[str, float]
    trend: str
    recommendations: Optional[List[str]] = None

class SentimentAnalysisRequest(BaseModel):
    text: str

class SentimentAnalysisResponse(BaseModel):
    sentiment: str
    confidence: float
    emotions: Dict[str, float]
