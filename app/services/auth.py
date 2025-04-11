from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.users import User
from app.utils.security import verify_password, decode_access_token, create_access_token

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.

    Args:
        db: Database session
        email: User email
        password: User password

    Returns:
        User object if authentication is successful, None otherwise
    """
    try:
        # Use raw SQL query to avoid SQLAlchemy enum validation
        result = db.execute(
            "SELECT * FROM users WHERE email = :email AND is_active = TRUE AND is_deleted = FALSE",
            {"email": email}
        ).fetchone()

        if not result:
            print(f"No user found with email: {email}")
            return None

        # Convert result to dict
        user_dict = {column: value for column, value in zip(result.keys(), result)}

        # Check password
        if not verify_password(password, user_dict['password_hash']):
            print(f"Invalid password for user: {email}")
            return None

        # Create a User object manually
        user = User()
        for key, value in user_dict.items():
            if hasattr(user, key):
                setattr(user, key, value)

        return user
    except Exception as e:
        print(f"Error in authenticate_user: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get the current authenticated user.

    Args:
        db: Database session
        token: JWT token

    Returns:
        User object

    Raises:
        HTTPException: If authentication fails
    """
    try:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        payload = decode_access_token(token)
        if payload is None:
            print("Token decode failed")
            raise credentials_exception

        user_id: str = payload.get("sub")
        if user_id is None:
            print("No user_id in token")
            raise credentials_exception

        print(f"Token payload: {payload}")
        print(f"Looking up user with ID: {user_id}")

        # Use direct psycopg2 connection to avoid SQLAlchemy issues
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

        # Get user data
        cur.execute(
            "SELECT * FROM users WHERE user_id = %s AND is_active = TRUE AND is_deleted = FALSE",
            (user_id,)
        )
        user_data = cur.fetchone()

        if not user_data:
            print(f"No user found with ID: {user_id}")
            conn.close()
            raise credentials_exception

        # Get column names
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'users'
            ORDER BY ordinal_position
        """)
        columns = [col[0] for col in cur.fetchall()]

        # Create user dict
        user_dict = dict(zip(columns, user_data))
        print(f"Found user: {user_dict['first_name']} {user_dict['last_name']}")

        # Update last login time
        cur.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s",
            (user_id,)
        )
        conn.commit()

        # Close the connection
        conn.close()

        # Create a User object manually
        user = User()
        for key, value in user_dict.items():
            if hasattr(user, key):
                setattr(user, key, value)

        return user
    except Exception as e:
        print(f"Error in get_current_user: {str(e)}")
        import traceback
        traceback.print_exc()
        raise credentials_exception

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        User object

    Raises:
        HTTPException: If the user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def check_user_role(user: User, required_role: str) -> bool:
    """
    Check if a user has a specific role.

    Args:
        user: User object
        required_role: Required role

    Returns:
        True if the user has the required role, False otherwise
    """
    roles = user.roles.split(",")
    return required_role in roles
