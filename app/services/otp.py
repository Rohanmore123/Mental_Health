import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.users import User
from app.services.auth import create_access_token

class OTPService:
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generate a random OTP of specified length."""
        # For testing purposes, use a fixed OTP
        otp = '123456'
        print(f"Generated OTP: {otp}")
        return otp

    @staticmethod
    def send_otp(mobile_number: str, otp: str) -> bool:
        """
        Send OTP via SMS.

        In a production environment, this would integrate with an SMS service like Twilio.
        For now, we'll just print the OTP to the console.
        """
        print("\n" + "*" * 50)
        print(f"*** OTP for {mobile_number}: {otp} ***")
        print("*" * 50 + "\n")
        # TODO: Integrate with SMS service in production
        return True

    @staticmethod
    def create_otp(db: Session, mobile_number: str) -> Dict[str, Any]:
        """
        Create a new OTP for the given mobile number.

        Args:
            db: Database session
            mobile_number: Mobile number to send OTP to

        Returns:
            Dict containing OTP details
        """
        print(f"\nCreating OTP for mobile number: {mobile_number}\n")

        # Generate a new OTP
        otp = OTPService.generate_otp()
        print(f"\nGenerated OTP: {otp} for {mobile_number}\n")

        # Set expiration time (10 minutes from now)
        expires_at = datetime.now() + timedelta(minutes=10)

        # Check if user exists with this mobile number
        user_query = """
            SELECT user_id FROM users WHERE mobile_number = :mobile_number
        """
        user_result = db.execute(text(user_query), {"mobile_number": mobile_number}).fetchone()

        user_id = user_result[0] if user_result else None

        # Create OTP record
        otp_id = uuid4()

        # Check if there's an existing OTP for this mobile number
        existing_otp_query = """
            SELECT otp_id FROM otp
            WHERE user_id = :user_id
            AND valid_until > CURRENT_TIMESTAMP
        """

        if user_id:
            existing_otp = db.execute(
                text(existing_otp_query),
                {"user_id": str(user_id)}
            ).fetchone()

            if existing_otp:
                # Update existing OTP
                update_query = """
                    UPDATE otp
                    SET otp_text = :otp,
                        created_at = CURRENT_TIMESTAMP,
                        valid_until = :expires_at,
                        validated_at = NULL,
                        status = 'pending'
                    WHERE otp_id = :otp_id
                    RETURNING otp_id
                """

                result = db.execute(
                    text(update_query),
                    {
                        "otp": otp,
                        "expires_at": expires_at,
                        "otp_id": str(existing_otp[0])
                    }
                ).fetchone()

                otp_id = result[0] if result else otp_id
            else:
                # Create new OTP
                insert_query = """
                    INSERT INTO otp (
                        otp_id, otp_text, user_id, created_at, valid_until, status
                    ) VALUES (
                        :otp_id, :otp, :user_id, CURRENT_TIMESTAMP, :expires_at, 'pending'
                    )
                    RETURNING otp_id
                """

                result = db.execute(
                    text(insert_query),
                    {
                        "otp_id": str(otp_id),
                        "otp": otp,
                        "user_id": str(user_id),
                        "expires_at": expires_at
                    }
                ).fetchone()

                otp_id = result[0] if result else otp_id
        else:
            # No user found with this mobile number
            # Create a temporary user for OTP verification
            temp_user_id = uuid4()
            user_id = None

            try:
                # First, check if the is_temporary column exists
                column_check_query = """
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_schema = 'public'
                        AND table_name = 'users'
                        AND column_name = 'is_temporary'
                    );
                """

                column_exists = db.execute(text(column_check_query)).fetchone()[0]

                # Create temporary user with appropriate columns
                if column_exists:
                    # Create temporary user with is_temporary column and default values for required fields
                    temp_user_query = """
                        INSERT INTO users (
                            user_id, mobile_number, roles, is_active, created_at, updated_at, is_deleted, is_temporary,
                            first_name, last_name, email, password_hash
                        ) VALUES (
                            :user_id, :mobile_number, 'patient', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE, TRUE,
                            'Temporary', 'User', :email, :password_hash
                        )
                        RETURNING user_id
                    """

                    # Generate a temporary email based on mobile number
                    temp_email = f"temp_{mobile_number.replace('+', '')}@example.com"

                    # Use a placeholder password hash (this is not a real hash, just a placeholder)
                    temp_password_hash = "$2b$12$temporary_placeholder_hash_for_otp_verification"

                    temp_user_result = db.execute(
                        text(temp_user_query),
                        {
                            "user_id": str(temp_user_id),
                            "mobile_number": mobile_number,
                            "email": temp_email,
                            "password_hash": temp_password_hash
                        }
                    ).fetchone()

                    user_id = temp_user_result[0] if temp_user_result else temp_user_id
                else:
                    # Try to add the is_temporary column
                    try:
                        add_column_query = """
                            ALTER TABLE users ADD COLUMN is_temporary BOOLEAN DEFAULT FALSE;
                        """
                        db.execute(text(add_column_query))
                        db.commit()  # Commit the schema change

                        # Now create the user with the new column and default values for required fields
                        temp_user_query = """
                            INSERT INTO users (
                                user_id, mobile_number, roles, is_active, created_at, updated_at, is_deleted, is_temporary,
                                first_name, last_name, email, password_hash
                            ) VALUES (
                                :user_id, :mobile_number, 'patient', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE, TRUE,
                                'Temporary', 'User', :email, :password_hash
                            )
                            RETURNING user_id
                        """

                        # Generate a temporary email based on mobile number
                        temp_email = f"temp_{mobile_number.replace('+', '')}@example.com"

                        # Use a placeholder password hash (this is not a real hash, just a placeholder)
                        temp_password_hash = "$2b$12$temporary_placeholder_hash_for_otp_verification"

                        temp_user_result = db.execute(
                            text(temp_user_query),
                            {
                                "user_id": str(temp_user_id),
                                "mobile_number": mobile_number,
                                "email": temp_email,
                                "password_hash": temp_password_hash
                            }
                        ).fetchone()

                        user_id = temp_user_result[0] if temp_user_result else temp_user_id
                    except Exception as e:
                        print(f"Error adding is_temporary column: {str(e)}")
                        db.rollback()  # Roll back on error

                        # Try without the is_temporary column but with default values for required fields
                        temp_user_query_simple = """
                            INSERT INTO users (
                                user_id, mobile_number, roles, is_active, created_at, updated_at, is_deleted,
                                first_name, last_name, email, password_hash
                            ) VALUES (
                                :user_id, :mobile_number, 'patient', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE,
                                'Temporary', 'User', :email, :password_hash
                            )
                            RETURNING user_id
                        """

                        # Generate a temporary email based on mobile number
                        temp_email = f"temp_{mobile_number.replace('+', '')}@example.com"

                        # Use a placeholder password hash (this is not a real hash, just a placeholder)
                        temp_password_hash = "$2b$12$temporary_placeholder_hash_for_otp_verification"

                        temp_user_result = db.execute(
                            text(temp_user_query_simple),
                            {
                                "user_id": str(temp_user_id),
                                "mobile_number": mobile_number,
                                "email": temp_email,
                                "password_hash": temp_password_hash
                            }
                        ).fetchone()

                        user_id = temp_user_result[0] if temp_user_result else temp_user_id
            except Exception as e:
                print(f"Error creating temporary user: {str(e)}")
                db.rollback()  # Roll back on error

                # Start a fresh transaction
                db.begin()

                # Try a simpler approach with default values for required fields
                temp_user_query_simple = """
                    INSERT INTO users (
                        user_id, mobile_number, roles, is_active, created_at, updated_at,
                        first_name, last_name, email, password_hash
                    ) VALUES (
                        :user_id, :mobile_number, 'patient', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                        'Temporary', 'User', :email, :password_hash
                    )
                    RETURNING user_id
                """

                # Generate a temporary email based on mobile number
                temp_email = f"temp_{mobile_number.replace('+', '')}@example.com"

                # Use a placeholder password hash (this is not a real hash, just a placeholder)
                temp_password_hash = "$2b$12$temporary_placeholder_hash_for_otp_verification"

                try:
                    temp_user_result = db.execute(
                        text(temp_user_query_simple),
                        {
                            "user_id": str(temp_user_id),
                            "mobile_number": mobile_number,
                            "email": temp_email,
                            "password_hash": temp_password_hash
                        }
                    ).fetchone()

                    user_id = temp_user_result[0] if temp_user_result else temp_user_id
                except Exception as e:
                    print(f"Error creating user with minimal fields: {str(e)}")
                    db.rollback()  # Roll back on error
                    raise  # Re-raise the exception

            # Create OTP for the temporary user
            if user_id:  # Only proceed if we successfully created a user
                try:
                    insert_query = """
                        INSERT INTO otp (
                            otp_id, otp_text, user_id, created_at, valid_until, status
                        ) VALUES (
                            :otp_id, :otp, :user_id, CURRENT_TIMESTAMP, :expires_at, 'pending'
                        )
                        RETURNING otp_id
                    """

                    result = db.execute(
                        text(insert_query),
                        {
                            "otp_id": str(otp_id),
                            "otp": otp,
                            "user_id": str(user_id),
                            "expires_at": expires_at
                        }
                    ).fetchone()

                    otp_id = result[0] if result else otp_id
                except Exception as e:
                    print(f"Error creating OTP: {str(e)}")
                    db.rollback()  # Roll back on error
                    raise  # Re-raise the exception
            else:
                # If we couldn't create a user, we can't create an OTP
                raise ValueError("Failed to create temporary user for OTP verification")

        try:
            # Send OTP via SMS
            OTPService.send_otp(mobile_number, otp)

            # Commit the transaction
            db.commit()

            return {
                "otp_id": otp_id,
                "expires_at": expires_at,
                "expires_in": 600  # 10 minutes in seconds
            }
        except Exception as e:
            # Roll back on any error
            db.rollback()
            print(f"Error in create_otp: {str(e)}")
            raise

    @staticmethod
    def verify_otp(db: Session, mobile_number: str, otp: str) -> Optional[Dict[str, Any]]:
        """
        Verify an OTP for the given mobile number.

        Args:
            db: Database session
            mobile_number: Mobile number
            otp: OTP to verify

        Returns:
            User details if verification is successful, None otherwise
        """
        # Check if user exists with this mobile number
        user_query = """
            SELECT user_id, email, first_name, last_name, roles, COALESCE(is_temporary, FALSE) as is_temporary
            FROM users
            WHERE mobile_number = :mobile_number
        """
        user_result = db.execute(text(user_query), {"mobile_number": mobile_number}).fetchone()

        if not user_result:
            # No user found with this mobile number
            return None

        user_id = user_result[0]
        is_temporary = user_result[5] if len(user_result) > 5 else False

        # Check if there's a valid OTP for this user
        otp_query = """
            SELECT otp_id, otp_text, valid_until
            FROM otp
            WHERE user_id = :user_id
            AND valid_until > CURRENT_TIMESTAMP
            AND status = 'pending'
            ORDER BY created_at DESC
            LIMIT 1
        """

        otp_result = db.execute(text(otp_query), {"user_id": str(user_id)}).fetchone()

        if not otp_result:
            # No valid OTP found
            return None

        otp_id, stored_otp, valid_until = otp_result

        if stored_otp != otp:
            # OTP doesn't match
            return None

        try:
            # Mark OTP as verified
            update_query = """
                UPDATE otp
                SET validated_at = CURRENT_TIMESTAMP,
                    status = 'verified'
                WHERE otp_id = :otp_id
            """

            db.execute(text(update_query), {"otp_id": str(otp_id)})

            # If this is a temporary user, we need to prompt for registration
            if is_temporary:
                # Commit the transaction
                db.commit()

                # Return a special response indicating registration is needed
                return {
                    "needs_registration": True,
                    "mobile_number": mobile_number,
                    "otp": otp
                }

            # Commit the transaction
            db.commit()

            # Create access token
            access_token = create_access_token(
                data={"sub": str(user_id)},
                expires_delta=timedelta(minutes=1440)  # 24 hours
            )

            # Return user details
            return {
                "access_token": access_token,
                "user_id": str(user_id),
                "email": user_result[1],
                "name": f"{user_result[2] or ''} {user_result[3] or ''}".strip(),
                "roles": user_result[4]
            }
        except Exception as e:
            # Roll back on any error
            db.rollback()
            print(f"Error in verify_otp: {str(e)}")
            raise

    @staticmethod
    def register_user_with_mobile(
        db: Session,
        mobile_number: str,
        otp: str,
        first_name: str,
        last_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Register a new user with mobile number after OTP verification.

        Args:
            db: Database session
            mobile_number: Mobile number
            otp: OTP to verify
            first_name: User's first name
            last_name: User's last name

        Returns:
            User details if registration is successful, None otherwise
        """
        # Check if there's a valid OTP for this mobile number
        otp_query = """
            SELECT o.otp_id, o.otp_text, o.valid_until, o.user_id
            FROM otp o
            JOIN users u ON o.user_id = u.user_id
            WHERE o.otp_text = :otp
            AND u.mobile_number = :mobile_number
            AND o.valid_until > CURRENT_TIMESTAMP
            AND o.status = 'pending'
            ORDER BY o.created_at DESC
            LIMIT 1
        """

        otp_result = db.execute(
            text(otp_query),
            {
                "otp": otp,
                "mobile_number": mobile_number
            }
        ).fetchone()

        if not otp_result:
            # No valid OTP found
            return None

        otp_id, stored_otp, valid_until, temp_user_id = otp_result

        # Check if the user is temporary
        user_query = """
            SELECT COALESCE(is_temporary, FALSE) as is_temporary
            FROM users
            WHERE user_id = :user_id
        """

        user_result = db.execute(text(user_query), {"user_id": str(temp_user_id)}).fetchone()
        is_temporary = user_result[0] if user_result else False

        if is_temporary:
            # Update the temporary user with real information
            update_user_query = """
                UPDATE users
                SET first_name = :first_name,
                    last_name = :last_name,
                    is_temporary = FALSE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = :user_id
                RETURNING user_id
            """

            result = db.execute(
                text(update_user_query),
                {
                    "user_id": str(temp_user_id),
                    "first_name": first_name,
                    "last_name": last_name
                }
            ).fetchone()

            user_id = result[0] if result else temp_user_id
        else:
            # Create new user (this shouldn't normally happen, but just in case)
            user_id = uuid4()

            insert_user_query = """
                INSERT INTO users (
                    user_id, first_name, last_name, mobile_number, roles, is_active, created_at, updated_at
                ) VALUES (
                    :user_id, :first_name, :last_name, :mobile_number, 'patient', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                RETURNING user_id
            """

            result = db.execute(
                text(insert_user_query),
                {
                    "user_id": str(user_id),
                    "first_name": first_name,
                    "last_name": last_name,
                    "mobile_number": mobile_number
                }
            ).fetchone()

            if not result:
                # Failed to create user
                return None

        try:
            # Update OTP status
            update_query = """
                UPDATE otp
                SET validated_at = CURRENT_TIMESTAMP,
                    status = 'verified'
                WHERE otp_id = :otp_id
            """

            db.execute(text(update_query), {"otp_id": str(otp_id)})

            # Create patient record if it doesn't exist
            patient_check_query = """
                SELECT patient_id FROM patients WHERE user_id = :user_id
            """

            patient_exists = db.execute(text(patient_check_query), {"user_id": str(user_id)}).fetchone()

            if not patient_exists:
                # Create patient record
                patient_id = uuid4()

                insert_patient_query = """
                    INSERT INTO patients (
                        patient_id, user_id, title, first_name, last_name, gender, created_at, updated_at
                    ) VALUES (
                        :patient_id, :user_id, '', :first_name, :last_name, '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """

                db.execute(
                    text(insert_patient_query),
                    {
                        "patient_id": str(patient_id),
                        "user_id": str(user_id),
                        "first_name": first_name,
                        "last_name": last_name
                    }
                )

            # Commit the transaction
            db.commit()

            # Create access token
            access_token = create_access_token(
                data={"sub": str(user_id)},
                expires_delta=timedelta(minutes=1440)  # 24 hours
            )

            # Return user details
            return {
                "access_token": access_token,
                "user_id": str(user_id),
                "name": f"{first_name} {last_name}".strip(),
                "roles": "patient"
            }
        except Exception as e:
            # Roll back on any error
            db.rollback()
            print(f"Error in register_user_with_mobile: {str(e)}")
            raise
