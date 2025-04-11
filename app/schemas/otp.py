from typing import Optional
from pydantic import BaseModel, Field, validator
import re

class OTPRequest(BaseModel):
    mobile_number: str = Field(..., description="Mobile number with country code (e.g., +1234567890)")

    @validator('mobile_number')
    def validate_mobile_number(cls, v):
        # Basic validation for mobile number format
        if not re.match(r'^\+?[1-9]\d{1,14}$', v):
            raise ValueError('Invalid mobile number format. Please include country code (e.g., +1234567890)')
        return v

class OTPVerify(BaseModel):
    mobile_number: str = Field(..., description="Mobile number with country code (e.g., +1234567890)")
    otp: str = Field(..., min_length=4, max_length=6, description="OTP code received via SMS")

    @validator('otp')
    def validate_otp(cls, v):
        if not v.isdigit():
            raise ValueError('OTP must contain only digits')
        return v

class OTPResponse(BaseModel):
    message: str
    expires_in: Optional[int] = None

class OTPVerifyResponse(BaseModel):
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    roles: Optional[str] = None
    needs_registration: Optional[bool] = None
    mobile_number: Optional[str] = None
    otp: Optional[str] = None
