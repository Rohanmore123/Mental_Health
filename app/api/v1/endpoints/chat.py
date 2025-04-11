from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.users import User
from app.services.auth import get_current_active_user
from app.schemas.chat import ChatMessage, ChatMessageCreate, ChatMessageList
from app.services.chat import ChatService

router = APIRouter()

@router.get("/messages", response_model=ChatMessageList)
def get_chat_messages(
    receiver_id: Optional[UUID] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get chat messages for the current user.
    
    If receiver_id is provided, returns messages between the current user and the specified receiver.
    Otherwise, returns all messages for the current user.
    """
    try:
        messages = ChatService.get_messages(
            db=db, 
            user_id=current_user.user_id, 
            receiver_id=receiver_id,
            limit=limit
        )
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving chat messages: {str(e)}"
        )

@router.post("/messages", response_model=ChatMessage)
def create_chat_message(
    message: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a new chat message.
    """
    try:
        # Set the sender_id to the current user's ID
        message_data = message.dict()
        message_data["sender_id"] = current_user.user_id
        
        # Create the message
        new_message = ChatService.create_message(db=db, message_data=message_data)
        return new_message
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating chat message: {str(e)}"
        )

@router.get("/contacts", response_model=List[Any])
def get_chat_contacts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get a list of contacts the current user can chat with.
    
    For patients, this includes doctors and AI.
    For doctors, this includes patients they have appointments with.
    """
    try:
        contacts = ChatService.get_contacts(db=db, user=current_user)
        return contacts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving chat contacts: {str(e)}"
        )
