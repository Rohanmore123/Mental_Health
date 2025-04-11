from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.otp import OTPRequest, OTPVerify, OTPResponse, OTPVerifyResponse
# Import the new OTP service
from app.services.otp_service import OTPService

router = APIRouter()

@router.get("/test")
def test_endpoint():
    """
    Simple test endpoint to verify that the OTP auth API is working.
    """
    print("Test endpoint called!")
    return {"status": "success", "message": "OTP auth API is working!"}

@router.post("/send", response_model=OTPResponse)
def send_otp(
    request: OTPRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Send OTP to the provided mobile number.
    """
    print(f"\nReceived OTP request for mobile number: {request.mobile_number}\n")

    try:
        print("Calling OTPService.create_otp...")
        result = OTPService.create_otp(db, request.mobile_number)
        print(f"OTP created successfully: {result}")

        response = {
            "message": f"OTP sent to {request.mobile_number}",
            "expires_in": result["expires_in"]
        }
        print(f"Returning response: {response}")
        return response
    except Exception as e:
        print(f"\nERROR in send_otp: {str(e)}\n")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending OTP: {str(e)}"
        )

@router.post("/verify", response_model=OTPVerifyResponse)
def verify_otp(
    request: OTPVerify,
    db: Session = Depends(get_db)
) -> Any:
    """
    Verify OTP and return access token if valid.
    """
    try:
        print(f"\nVerifying OTP: {request.otp} for mobile: {request.mobile_number}\n")

        result = OTPService.verify_otp(db, request.mobile_number, request.otp)

        print(f"OTP verification result: {result}")

        if not result:
            print("OTP verification failed - Invalid OTP or mobile number")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid OTP or mobile number"
            )

        # Check if registration is needed
        if result.get("needs_registration"):
            print("User needs registration")
            return {
                "needs_registration": True,
                "mobile_number": result.get("mobile_number"),
                "otp": result.get("otp")
            }

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying OTP: {str(e)}"
        )

class RegistrationRequest(OTPVerify):
    first_name: str
    last_name: str

@router.post("/register", response_model=OTPVerifyResponse)
def register_with_otp(
    request: RegistrationRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user with mobile number after OTP verification.
    """
    try:
        # We don't need to check if the user exists here, as the OTP service will handle that
        # The OTP service will update the temporary user if it exists, or create a new one if needed

        result = OTPService.register_user_with_mobile(
            db,
            request.mobile_number,
            request.otp,
            request.first_name,
            request.last_name
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid OTP or mobile number"
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering user: {str(e)}"
        )
