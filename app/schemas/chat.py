from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class ChatMessageBase(BaseModel):
    message_text: str
    attachment_url: Optional[str] = None

class ChatMessageCreate(ChatMessageBase):
    receiver_id: Optional[UUID] = None

class ChatMessage(ChatMessageBase):
    chat_message_id: UUID
    sender_id: Optional[UUID] = None
    receiver_id: Optional[UUID] = None
    timestamp: datetime
    
    class Config:
        orm_mode = True

class ChatMessageList(BaseModel):
    messages: List[ChatMessage]
    
    class Config:
        orm_mode = True

class ChatContact(BaseModel):
    user_id: UUID
    name: str
    role: str
    profile_image: Optional[str] = None
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int = 0
    
    class Config:
        orm_mode = True
