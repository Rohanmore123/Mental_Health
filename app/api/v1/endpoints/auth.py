from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.users import User
from app.schemas.users import UserCreate, UserResponse
from app.services.auth import authenticate_user
from app.utils.security import create_access_token, get_password_hash, verify_password

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user.
    """
    # Check if user with this email already exists
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    db_user = User(
        title=user_in.title,
        first_name=user_in.first_name,
        middle_name=user_in.middle_name,
        last_name=user_in.last_name,
        gender=user_in.gender,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        roles=user_in.roles,
        profile_picture=user_in.profile_picture
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@router.post("/login")
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    try:
        print(f"Login attempt for user: {form_data.username}")

        # Create a simple login function that doesn't rely on SQLAlchemy models
        import psycopg2
        from urllib.parse import unquote
        from app.config import settings

        # Parse the connection string
        db_url = settings.DATABASE_URL
        parts = db_url.split("://")[1].split("@")
        user_pass = parts[0].split(":")
        host_port_db = parts[1].split("/")
        host_port = host_port_db[0].split(":")

        username = user_pass[0]
        password = unquote(user_pass[1]) if "%" in user_pass[1] else user_pass[1]
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else "5432"
        database = host_port_db[1]

        # Connect to the database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )

        # Create a cursor
        cur = conn.cursor()

        # Check if user exists
        cur.execute(
            "SELECT * FROM users WHERE email = %s AND is_active = TRUE AND is_deleted = FALSE",
            (form_data.username,)
        )
        user = cur.fetchone()

        if not user:
            print(f"No user found with email: {form_data.username}")
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Define column names based on the database schema
        columns = ['user_id', 'title', 'first_name', 'middle_name', 'last_name', 'gender', 'email', 'password_hash', 'roles', 'profile_picture', 'is_active', 'last_login', 'is_deleted', 'created_at', 'updated_at']

        # Create user dict
        user_dict = {}
        for i, col in enumerate(columns):
            if i < len(user):
                user_dict[col] = user[i]

        # Check password
        if not verify_password(form_data.password, user_dict['password_hash']):
            print(f"Invalid password for user: {form_data.username}")
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Close the connection
        conn.close()

        # Create access token with user information
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        # Add user information to the token
        extra_data = {
            "email": user_dict['email'],
            "roles": user_dict['roles'],
            "name": f"{user_dict['first_name']} {user_dict['last_name']}".strip()
        }

        access_token = create_access_token(
            subject=str(user_dict['user_id']),
            expires_delta=access_token_expires,
            extra_data=extra_data
        )

        print(f"Login successful for user: {form_data.username}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": str(user_dict['user_id']),
            "email": user_dict['email'],
            "name": f"{user_dict['first_name']} {user_dict['last_name']}".strip(),
            "roles": user_dict['roles']
        }
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        print(f"Error during login: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
