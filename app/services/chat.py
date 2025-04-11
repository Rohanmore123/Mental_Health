from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.users import User

class ChatService:
    @staticmethod
    def get_messages(
        db: Session, 
        user_id: UUID, 
        receiver_id: Optional[UUID] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get chat messages for a user.
        
        If receiver_id is provided, returns messages between the user and the specified receiver.
        Otherwise, returns all messages for the user.
        """
        query = """
            SELECT 
                cm.chat_message_id,
                cm.sender_id,
                cm.receiver_id,
                cm.message_text,
                cm.timestamp,
                cm.attachment_url
            FROM 
                chat_messages cm
            WHERE 
                (cm.sender_id = :user_id OR cm.receiver_id = :user_id)
        """
        
        params = {"user_id": str(user_id)}
        
        if receiver_id:
            query += """
                AND (
                    (cm.sender_id = :receiver_id AND cm.receiver_id = :user_id)
                    OR
                    (cm.sender_id = :user_id AND cm.receiver_id = :receiver_id)
                )
            """
            params["receiver_id"] = str(receiver_id)
        
        query += """
            ORDER BY cm.timestamp DESC
            LIMIT :limit
        """
        params["limit"] = limit
        
        result = db.execute(text(query), params).fetchall()
        
        # Convert to list of dictionaries
        messages = []
        for row in result:
            message = {
                "chat_message_id": row[0],
                "sender_id": row[1],
                "receiver_id": row[2],
                "message_text": row[3],
                "timestamp": row[4],
                "attachment_url": row[5]
            }
            messages.append(message)
        
        # Reverse to get chronological order
        messages.reverse()
        
        return messages
    
    @staticmethod
    def create_message(db: Session, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new chat message.
        """
        # Generate a UUID for the message
        message_id = uuid4()
        
        # Set the timestamp
        timestamp = datetime.now()
        
        # Create the SQL query
        query = """
            INSERT INTO chat_messages (
                chat_message_id, sender_id, receiver_id, message_text, 
                timestamp, attachment_url
            ) VALUES (
                :chat_message_id, :sender_id, :receiver_id, :message_text, 
                :timestamp, :attachment_url
            ) RETURNING 
                chat_message_id, sender_id, receiver_id, message_text, 
                timestamp, attachment_url
        """
        
        # Set up the parameters
        params = {
            "chat_message_id": str(message_id),
            "sender_id": str(message_data["sender_id"]) if message_data.get("sender_id") else None,
            "receiver_id": str(message_data["receiver_id"]) if message_data.get("receiver_id") else None,
            "message_text": message_data["message_text"],
            "timestamp": timestamp,
            "attachment_url": message_data.get("attachment_url")
        }
        
        # Execute the query
        result = db.execute(text(query), params).fetchone()
        
        # Convert to dictionary
        message = {
            "chat_message_id": result[0],
            "sender_id": result[1],
            "receiver_id": result[2],
            "message_text": result[3],
            "timestamp": result[4],
            "attachment_url": result[5]
        }
        
        # Commit the transaction
        db.commit()
        
        return message
    
    @staticmethod
    def get_contacts(db: Session, user: User) -> List[Dict[str, Any]]:
        """
        Get a list of contacts the user can chat with.
        
        For patients, this includes doctors and AI.
        For doctors, this includes patients they have appointments with.
        """
        contacts = []
        
        # Check if the user is a patient or doctor
        roles = user.roles.split(",") if user.roles else []
        
        if "patient" in roles:
            # Get doctors the patient has appointments with
            query = """
                SELECT DISTINCT
                    d.doctor_id AS user_id,
                    CONCAT(d.title, ' ', d.first_name, ' ', d.last_name) AS name,
                    'doctor' AS role,
                    NULL AS profile_image,
                    (
                        SELECT cm.message_text
                        FROM chat_messages cm
                        WHERE 
                            (cm.sender_id = d.doctor_id AND cm.receiver_id = :user_id)
                            OR
                            (cm.sender_id = :user_id AND cm.receiver_id = d.doctor_id)
                        ORDER BY cm.timestamp DESC
                        LIMIT 1
                    ) AS last_message,
                    (
                        SELECT cm.timestamp
                        FROM chat_messages cm
                        WHERE 
                            (cm.sender_id = d.doctor_id AND cm.receiver_id = :user_id)
                            OR
                            (cm.sender_id = :user_id AND cm.receiver_id = d.doctor_id)
                        ORDER BY cm.timestamp DESC
                        LIMIT 1
                    ) AS last_message_time,
                    (
                        SELECT COUNT(*)
                        FROM chat_messages cm
                        WHERE 
                            cm.sender_id = d.doctor_id
                            AND cm.receiver_id = :user_id
                            AND cm.timestamp > (
                                SELECT COALESCE(MAX(timestamp), '1900-01-01'::timestamp)
                                FROM chat_messages
                                WHERE sender_id = :user_id AND receiver_id = d.doctor_id
                            )
                    ) AS unread_count
                FROM 
                    doctors d
                JOIN 
                    appointments a ON d.doctor_id = a.doctor_id
                JOIN 
                    patients p ON a.patient_id = p.patient_id
                JOIN 
                    users u ON p.user_id = u.user_id
                WHERE 
                    u.user_id = :user_id
                ORDER BY 
                    last_message_time DESC NULLS LAST
            """
            
            doctor_contacts = db.execute(
                text(query), 
                {"user_id": str(user.user_id)}
            ).fetchall()
            
            for row in doctor_contacts:
                contact = {
                    "user_id": row[0],
                    "name": row[1],
                    "role": row[2],
                    "profile_image": row[3],
                    "last_message": row[4],
                    "last_message_time": row[5],
                    "unread_count": row[6] or 0
                }
                contacts.append(contact)
            
            # Add AI as a contact
            ai_contact = {
                "user_id": None,
                "name": "AI Health Assistant",
                "role": "ai",
                "profile_image": None,
                "last_message": None,
                "last_message_time": None,
                "unread_count": 0
            }
            
            # Get last AI message
            ai_query = """
                SELECT 
                    message_text, 
                    timestamp
                FROM 
                    chat_messages
                WHERE 
                    (sender_id IS NULL AND receiver_id = :user_id)
                    OR
                    (sender_id = :user_id AND receiver_id IS NULL)
                ORDER BY 
                    timestamp DESC
                LIMIT 1
            """
            
            ai_result = db.execute(
                text(ai_query), 
                {"user_id": str(user.user_id)}
            ).fetchone()
            
            if ai_result:
                ai_contact["last_message"] = ai_result[0]
                ai_contact["last_message_time"] = ai_result[1]
            
            contacts.append(ai_contact)
            
        elif "doctor" in roles:
            # Get patients the doctor has appointments with
            query = """
                SELECT DISTINCT
                    p.patient_id AS user_id,
                    CONCAT(p.title, ' ', p.first_name, ' ', p.last_name) AS name,
                    'patient' AS role,
                    NULL AS profile_image,
                    (
                        SELECT cm.message_text
                        FROM chat_messages cm
                        WHERE 
                            (cm.sender_id = p.patient_id AND cm.receiver_id = :user_id)
                            OR
                            (cm.sender_id = :user_id AND cm.receiver_id = p.patient_id)
                        ORDER BY cm.timestamp DESC
                        LIMIT 1
                    ) AS last_message,
                    (
                        SELECT cm.timestamp
                        FROM chat_messages cm
                        WHERE 
                            (cm.sender_id = p.patient_id AND cm.receiver_id = :user_id)
                            OR
                            (cm.sender_id = :user_id AND cm.receiver_id = p.patient_id)
                        ORDER BY cm.timestamp DESC
                        LIMIT 1
                    ) AS last_message_time,
                    (
                        SELECT COUNT(*)
                        FROM chat_messages cm
                        WHERE 
                            cm.sender_id = p.patient_id
                            AND cm.receiver_id = :user_id
                            AND cm.timestamp > (
                                SELECT COALESCE(MAX(timestamp), '1900-01-01'::timestamp)
                                FROM chat_messages
                                WHERE sender_id = :user_id AND receiver_id = p.patient_id
                            )
                    ) AS unread_count
                FROM 
                    patients p
                JOIN 
                    appointments a ON p.patient_id = a.patient_id
                JOIN 
                    doctors d ON a.doctor_id = d.doctor_id
                JOIN 
                    users u ON d.user_id = u.user_id
                WHERE 
                    u.user_id = :user_id
                ORDER BY 
                    last_message_time DESC NULLS LAST
            """
            
            patient_contacts = db.execute(
                text(query), 
                {"user_id": str(user.user_id)}
            ).fetchall()
            
            for row in patient_contacts:
                contact = {
                    "user_id": row[0],
                    "name": row[1],
                    "role": row[2],
                    "profile_image": row[3],
                    "last_message": row[4],
                    "last_message_time": row[5],
                    "unread_count": row[6] or 0
                }
                contacts.append(contact)
        
        return contacts
