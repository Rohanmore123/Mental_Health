from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import base64

from app.database import get_db
from app.models.users import User
from app.schemas.communication import AIChatRequest, AIChatResponse, SentimentAnalysisRequest, SentimentAnalysisResponse
from app.services.auth import get_current_active_user
from app.services.ai_chat import AIChatService
from app.services.analytics import AnalyticsService

router = APIRouter()

@router.post("/text", response_model=AIChatResponse)
async def chat_with_ai_text(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Chat with AI using text.
    """
    # Extract message from request body
    message = request.get('message', '')
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message is required"
        )

    # Create AI chat request
    chat_request = AIChatRequest(
        user_id=current_user.user_id,
        message=message
    )

    response = await AIChatService.process_chat(db, chat_request)
    return response

@router.post("/audio", response_model=AIChatResponse)
async def chat_with_ai_audio(
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Chat with AI using audio.
    """
    # Read audio file
    audio_data = await audio_file.read()

    # Encode audio data to base64
    base64_audio = base64.b64encode(audio_data).decode("utf-8")

    request = AIChatRequest(
        user_id=current_user.user_id,
        message="",  # Will be transcribed from audio
        audio_file=base64_audio
    )

    response = await AIChatService.process_chat(db, request)
    return response

@router.post("/sentiment", response_model=SentimentAnalysisResponse)
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Analyze sentiment of text.
    """
    result = AnalyticsService.analyze_sentiment(request)

    return SentimentAnalysisResponse(
        sentiment=result["sentiment"],
        confidence=result["confidence"],
        emotions=result["emotions"]
    )
