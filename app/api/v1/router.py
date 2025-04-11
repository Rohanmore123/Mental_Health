from fastapi import APIRouter

from app.api.v1.endpoints import auth, doctors, ai_chat, analytics, users, patients, chat, otp_auth

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(otp_auth.router, prefix="/otp-auth", tags=["otp-authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["doctors"])
api_router.include_router(ai_chat.router, prefix="/ai-chat", tags=["ai-chat"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
