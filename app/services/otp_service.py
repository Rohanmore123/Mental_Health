import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

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

        try:
            # Check if user exists with this mobile number
            user_query = """
                SELECT user_id FROM users WHERE mobile_number = :mobile_number
            """
            user_result = db.execute(text(user_query), {"mobile_number": mobile_number}).fetchone()

            if user_result:
                user_id = user_result[0]
                print(f"Found existing user with ID: {user_id}")
            else:
                # Check if a temporary user with the same email already exists
                temp_email = f"temp_{mobile_number.replace('+', '')}@example.com"

                email_query = """
                    SELECT user_id FROM users WHERE email = :email
                """
                email_result = db.execute(text(email_query), {"email": temp_email}).fetchone()

                if email_result:
                    user_id = email_result[0]
                    print(f"Found existing user with email {temp_email}, ID: {user_id}")

                    # Update the mobile number
                    update_query = """
                        UPDATE users
                        SET mobile_number = :mobile_number,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = :user_id
                        RETURNING user_id
                    """

                    result = db.execute(
                        text(update_query),
                        {
                            "mobile_number": mobile_number,
                            "user_id": str(user_id)
                        }
                    ).fetchone()

                    user_id = result[0] if result else user_id
                    print(f"Updated user with ID: {user_id}")
                else:
                    # Create a new temporary user
                    user_id = str(uuid4())
                    print(f"Creating new user with ID: {user_id}")

                    # Use a placeholder password hash
                    temp_password_hash = "$2b$12$temporary_placeholder_hash_for_otp_verification"

                    insert_user_query = """
                        INSERT INTO users (
                            user_id, mobile_number, roles, is_active, created_at, updated_at,
                            first_name, last_name, email, password_hash
                        ) VALUES (
                            :user_id, :mobile_number, 'patient', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                            'Temporary', 'User', :email, :password_hash
                        )
                        RETURNING user_id
                    """

                    result = db.execute(
                        text(insert_user_query),
                        {
                            "user_id": user_id,
                            "mobile_number": mobile_number,
                            "email": temp_email,
                            "password_hash": temp_password_hash
                        }
                    ).fetchone()

                    user_id = result[0] if result else user_id
                    print(f"Created new user with ID: {user_id}")

            # Check if there's an existing OTP for this user
            otp_query = """
                SELECT otp_id FROM otp
                WHERE user_id = :user_id
                AND valid_until > CURRENT_TIMESTAMP
            """

            existing_otp = db.execute(
                text(otp_query),
                {"user_id": str(user_id)}
            ).fetchone()

            if existing_otp:
                otp_id = existing_otp[0]
                print(f"Found existing OTP with ID: {otp_id}")

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
                        "otp_id": str(otp_id)
                    }
                ).fetchone()

                otp_id = result[0] if result else otp_id
                print(f"Updated OTP with ID: {otp_id}")
            else:
                # Create new OTP
                otp_id = str(uuid4())
                print(f"Creating new OTP with ID: {otp_id}")

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
                        "otp_id": otp_id,
                        "otp": otp,
                        "user_id": str(user_id),
                        "expires_at": expires_at
                    }
                ).fetchone()

                otp_id = result[0] if result else otp_id
                print(f"Created new OTP with ID: {otp_id}")

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
        try:
            print(f"\nVerifying OTP in service: {otp} for mobile: {mobile_number}\n")

            # Check if user exists with this mobile number
            user_query = text("""
                SELECT user_id, email, first_name, last_name, roles, COALESCE(is_temporary, FALSE) as is_temporary
                FROM users
                WHERE mobile_number = :mobile_number
            """)

            print(f"Executing user query: {user_query}")
            print(f"With parameters: mobile_number={mobile_number}")

            user_result = db.execute(user_query, {"mobile_number": mobile_number}).fetchone()

            print(f"User query result: {user_result}")

            if not user_result:
                print("No user found with this mobile number")

                # Let's check if any users exist with similar mobile numbers
                check_users_query = text("""
                    SELECT user_id, mobile_number, first_name, last_name
                    FROM users
                    WHERE mobile_number LIKE :mobile_pattern
                    LIMIT 10
                """)

                similar_users = db.execute(check_users_query, {"mobile_pattern": f"%{mobile_number[-8:]}%"}).fetchall()
                print(f"Found {len(similar_users)} users with similar mobile numbers:")
                for u in similar_users:
                    print(f"  - User ID: {u[0]}, Mobile: {u[1]}, Name: {u[2]} {u[3]}")

                # No user found with this mobile number
                return None

            user_id = user_result[0]
            is_temporary = user_result[5] if len(user_result) > 5 else False

            print(f"Found user with ID: {user_id}, is_temporary: {is_temporary}")

            # Check if there's a valid OTP for this user
            otp_query = text("""
                SELECT otp_id, otp_text, valid_until
                FROM otp
                WHERE user_id = :user_id
                AND valid_until > CURRENT_TIMESTAMP
                AND status = 'pending'
                ORDER BY created_at DESC
                LIMIT 1
            """)

            print(f"Executing OTP query: {otp_query}")
            print(f"With parameters: user_id={user_id}")

            otp_result = db.execute(otp_query, {"user_id": str(user_id)}).fetchone()

            print(f"OTP query result: {otp_result}")

            if not otp_result:
                print("No valid OTP found for this user")

                # Let's check if there are any OTPs for this user
                check_otps_query = text("""
                    SELECT otp_id, otp_text, valid_until, status, created_at
                    FROM otp
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT 5
                """)

                user_otps = db.execute(check_otps_query, {"user_id": str(user_id)}).fetchall()
                print(f"Found {len(user_otps)} OTPs for user {user_id}:")
                for o in user_otps:
                    print(f"  - OTP ID: {o[0]}, OTP: {o[1]}, Valid until: {o[2]}, Status: {o[3]}, Created: {o[4]}")

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
                if is_temporary or (user_result[2] == 'Temporary' and user_result[3] == 'User'):
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
                    subject=str(user_id),
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
        except Exception as e:
            print(f"Error in verify_otp: {str(e)}")
            db.rollback()
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
        try:
            print(f"\nAttempting to register user with mobile: {mobile_number}, OTP: {otp}\n")

            # Check if there's a valid OTP for this mobile number
            otp_query = text("""
                SELECT o.otp_id, o.otp_text, o.valid_until, o.user_id
                FROM otp o
                JOIN users u ON o.user_id = u.user_id
                WHERE o.otp_text = :otp
                AND u.mobile_number = :mobile_number
                AND o.valid_until > CURRENT_TIMESTAMP
                AND o.status = 'pending'
                ORDER BY o.created_at DESC
                LIMIT 1
            """)

            print(f"Executing OTP query: {otp_query}")
            print(f"With parameters: otp={otp}, mobile_number={mobile_number}")

            otp_result = db.execute(
                otp_query,
                {
                    "otp": otp,
                    "mobile_number": mobile_number
                }
            ).fetchone()

            print(f"OTP query result: {otp_result}")

            if not otp_result:
                print("No valid OTP found for this mobile number and OTP combination")

                # Let's check if the OTP exists at all
                check_otp_query = text("""
                    SELECT o.otp_id, o.otp_text, o.valid_until, o.user_id, u.mobile_number
                    FROM otp o
                    JOIN users u ON o.user_id = u.user_id
                    WHERE o.otp_text = :otp
                    ORDER BY o.created_at DESC
                    LIMIT 5
                """)

                check_results = db.execute(check_otp_query, {"otp": otp}).fetchall()
                print(f"Found {len(check_results)} OTPs with code {otp}:")
                for r in check_results:
                    print(f"  - OTP ID: {r[0]}, User ID: {r[3]}, Mobile: {r[4]}")

                # Let's also check if the user exists
                check_user_query = text("""
                    SELECT user_id, mobile_number, first_name, last_name
                    FROM users
                    WHERE mobile_number = :mobile_number
                """)

                user_results = db.execute(check_user_query, {"mobile_number": mobile_number}).fetchall()
                print(f"Found {len(user_results)} users with mobile {mobile_number}:")
                for r in user_results:
                    print(f"  - User ID: {r[0]}, Mobile: {r[1]}, Name: {r[2]} {r[3]}")

                # No valid OTP found
                return None

            otp_id, stored_otp, valid_until, temp_user_id = otp_result

            # Check if the user is temporary
            user_query = text("""
                SELECT first_name, last_name
                FROM users
                WHERE user_id = :user_id
            """)

            user_result = db.execute(user_query, {"user_id": str(temp_user_id)}).fetchone()
            is_temporary = user_result[0] == 'Temporary' and user_result[1] == 'User'

            if is_temporary:
                # Update the temporary user with real information
                update_user_query = text("""
                    UPDATE users
                    SET first_name = :first_name,
                        last_name = :last_name,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = :user_id
                    RETURNING user_id
                """)

                result = db.execute(
                    update_user_query,
                    {
                        "user_id": str(temp_user_id),
                        "first_name": first_name,
                        "last_name": last_name
                    }
                ).fetchone()

                user_id = result[0] if result else temp_user_id
            else:
                # Create new user (this shouldn't normally happen, but just in case)
                user_id = str(uuid4())

                insert_user_query = text("""
                    INSERT INTO users (
                        user_id, first_name, last_name, mobile_number, roles, is_active, created_at, updated_at
                    ) VALUES (
                        :user_id, :first_name, :last_name, :mobile_number, 'patient', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                    RETURNING user_id
                """)

                result = db.execute(
                    insert_user_query,
                    {
                        "user_id": user_id,
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
                update_query = text("""
                    UPDATE otp
                    SET validated_at = CURRENT_TIMESTAMP,
                        status = 'verified'
                    WHERE otp_id = :otp_id
                """)

                db.execute(update_query, {"otp_id": str(otp_id)})

                # Create patient record if it doesn't exist
                patient_check_query = text("""
                    SELECT patient_id FROM patients WHERE user_id = :user_id
                """)

                patient_exists = db.execute(patient_check_query, {"user_id": str(user_id)}).fetchone()

                if not patient_exists:
                    # Create patient record
                    patient_id = str(uuid4())

                    insert_patient_query = text("""
                        INSERT INTO patients (
                            patient_id, user_id, title, first_name, last_name, gender, created_at, updated_at
                        ) VALUES (
                            :patient_id, :user_id, '', :first_name, :last_name, 'Other', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                    """)

                    db.execute(
                        insert_patient_query,
                        {
                            "patient_id": patient_id,
                            "user_id": str(user_id),
                            "first_name": first_name,
                            "last_name": last_name
                        }
                    )

                # Commit the transaction
                db.commit()

                # Create access token
                access_token = create_access_token(
                    subject=str(user_id),
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
        except Exception as e:
            print(f"Error in register_user_with_mobile: {str(e)}")
            db.rollback()
            raise
