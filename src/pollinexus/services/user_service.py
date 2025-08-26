"""
User service for Pollinexus API.

This module provides user management, authentication, and authorization
functionality using DuckDB as the database backend.
"""

import hashlib
import uuid
import logging
import traceback
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from fastapi import HTTPException
from sqlalchemy import text

from ..core.logging import logger
from ..core.database import get_db
from ..core.config import settings


class UserService:
    """Service class for handling all user-related operations"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return UserService.hash_password(password) == hashed_password
    
    @staticmethod
    def generate_otp() -> str:
        """Generate a 6-digit OTP"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    @staticmethod
    def create_user(full_name: str, email: str, phone: str, password: Optional[str] = None) -> Dict:
        """Create a new user"""
        try:
            user_id = str(uuid.uuid4())
            hashed_password = UserService.hash_password(password) if password else None
            
            db = next(get_db())
            
            # Check if user already exists
            result = db.execute(
                text("SELECT COUNT(*) FROM users WHERE email = :email OR phone = :phone"),
                {"email": email, "phone": phone}
            ).fetchone()
            
            if result[0] > 0:
                raise HTTPException(
                    status_code=400,
                    detail="A user with this email or phone number already exists."
                )
            
            # Insert new user
            db.execute(
                text("""
                    INSERT INTO users (user_id, full_name, email, phone, password_hash, is_verified, is_deleted, role, created_at)
                    VALUES (:user_id, :full_name, :email, :phone, :password_hash, :is_verified, :is_deleted, :role, :created_at)
                """),
                {
                    "user_id": user_id,
                    "full_name": full_name,
                    "email": email,
                    "phone": phone,
                    "password_hash": hashed_password,
                    "is_verified": False,
                    "is_deleted": False,
                    "role": 'user',
                    "created_at": datetime.utcnow()
                }
            )
            
            db.commit()
            
            return {
                "user_id": user_id,
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "is_verified": False,
                "role": 'user'
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict]:
        """Get user by email"""
        try:
            db = next(get_db())
            
            result = db.execute(
                text("""
                    SELECT user_id, full_name, email, phone, password_hash, is_verified, is_deleted, role, created_at
                    FROM users WHERE email = :email
                """),
                {"email": email}
            ).fetchone()
            
            if result:
                return {
                    "user_id": str(result[0]),
                    "full_name": result[1],
                    "email": result[2],
                    "phone": result[3],
                    "password_hash": result[4],
                    "is_verified": result[5],
                    "is_deleted": result[6],
                    "role": result[7],
                    "created_at": result[8]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    @staticmethod
    def get_user_by_phone(phone: str) -> Optional[Dict]:
        """Get user by phone number"""
        try:
            db = next(get_db())
            
            result = db.execute(
                text("""
                    SELECT user_id, full_name, email, phone, password_hash, is_verified, is_deleted, role, created_at
                    FROM users WHERE phone = :phone
                """),
                {"phone": phone}
            ).fetchone()
            
            if result:
                return {
                    "user_id": str(result[0]),
                    "full_name": result[1],
                    "email": result[2],
                    "phone": result[3],
                    "password_hash": result[4],
                    "is_verified": result[5],
                    "is_deleted": result[6],
                    "role": result[7],
                    "created_at": result[8]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by phone: {e}")
            return None
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        try:
            db = next(get_db())
            
            result = db.execute(
                text("""
                    SELECT user_id, full_name, email, phone, password_hash, is_verified, is_deleted, role, created_at
                    FROM users WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            ).fetchone()
            
            if result:
                return {
                    "user_id": str(result[0]),
                    "full_name": result[1],
                    "email": result[2],
                    "phone": result[3],
                    "password_hash": result[4],
                    "is_verified": result[5],
                    "is_deleted": result[6],
                    "role": result[7],
                    "created_at": result[8]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    @staticmethod
    def get_all_users(page: int = 1, size: int = 100) -> Dict:
        """Get all users with pagination"""
        try:
            offset = (page - 1) * size
            
            db = next(get_db())
            
            # Get total count
            total_result = db.execute(
                text("SELECT COUNT(*) FROM users WHERE is_deleted = FALSE")
            ).fetchone()
            total = total_result[0] if total_result else 0
            
            # Get users
            results = db.execute(
                text("""
                    SELECT user_id, full_name, email, phone, is_verified, created_at
                    FROM users 
                    WHERE is_deleted = FALSE
                    ORDER BY created_at DESC
                    LIMIT :size OFFSET :offset
                """),
                {"size": size, "offset": offset}
            ).fetchall()
            
            users = []
            for row in results:
                user_id, full_name, email, phone, is_verified, created_at = row
                
                # Split full_name into first_name and last_name
                name_parts = (full_name or "").strip().split()
                first_name = name_parts[0] if name_parts else ""
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                
                users.append({
                    "id": str(user_id),
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone": phone,
                    "verified": bool(is_verified),
                    "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)
                })
            
            return {
                "users": users,
                "total": int(total),
                "page": page,
                "size": size
            }
            
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            logger.error(traceback.format_exc())
            return {"users": [], "total": 0, "page": page, "size": size}

    @staticmethod
    def update_user(user_id: str, **kwargs) -> bool:
        """Update user information"""
        try:
            valid_fields = ['full_name', 'email', 'phone', 'is_verified', 'is_deleted', 'role']
            update_fields = {k: v for k, v in kwargs.items() if k in valid_fields and v is not None}
            
            if not update_fields:
                return False
            
            db = next(get_db())
            
            set_clause = ", ".join([f"{field} = :{field}" for field in update_fields.keys()])
            update_fields["user_id"] = user_id
            
            db.execute(
                text(f"UPDATE users SET {set_clause} WHERE user_id = :user_id"),
                update_fields
            )
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    @staticmethod
    def create_otp(user_id: str, email: Optional[str] = None, phone: Optional[str] = None, expires_in_minutes: int = 5) -> str:
        """Create and store OTP for user"""
        try:
            if not email and not phone:
                raise HTTPException(status_code=400, detail="Email or phone is required for OTP")
            
            otp = UserService.generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
            
            db = next(get_db())
            
            # Clear any existing unused OTPs for this user
            db.execute(
                text("DELETE FROM user_otps WHERE user_id = :user_id AND is_used = FALSE"),
                {"user_id": user_id}
            )
            
            # Insert new OTP
            db.execute(
                text("""
                    INSERT INTO user_otps (user_id, email, phone, otp, expires_at, created_at)
                    VALUES (:user_id, :email, :phone, :otp, :expires_at, :created_at)
                """),
                {
                    "user_id": user_id,
                    "email": email,
                    "phone": phone,
                    "otp": otp,
                    "expires_at": expires_at,
                    "created_at": datetime.utcnow()
                }
            )
            
            db.commit()
            return otp
            
        except Exception as e:
            logger.error(f"Error creating OTP: {e}")
            raise HTTPException(status_code=500, detail="Failed to create OTP")
    
    @staticmethod
    def verify_otp(email: Optional[str] = None, phone: Optional[str] = None, otp: Optional[str] = None) -> Optional[str]:
        """Verify OTP and return user_id if valid"""
        try:
            if not email and not phone:
                raise HTTPException(status_code=400, detail="Email or phone is required for OTP verification")
            
            if not otp:
                raise HTTPException(status_code=400, detail="OTP is required")
            
            db = next(get_db())
            
            if email:
                result = db.execute(
                    text("""
                        SELECT user_id FROM user_otps 
                        WHERE email = :email AND otp = :otp AND is_used = FALSE AND expires_at > :now
                    """),
                    {"email": email, "otp": otp, "now": datetime.utcnow()}
                ).fetchone()
            else:
                result = db.execute(
                    text("""
                        SELECT user_id FROM user_otps 
                        WHERE phone = :phone AND otp = :otp AND is_used = FALSE AND expires_at > :now
                    """),
                    {"phone": phone, "otp": otp, "now": datetime.utcnow()}
                ).fetchone()
            
            if result:
                user_id = result[0]
                
                # Mark OTP as used
                if email:
                    db.execute(
                        text("UPDATE user_otps SET is_used = TRUE WHERE email = :email AND otp = :otp"),
                        {"email": email, "otp": otp}
                    )
                else:
                    db.execute(
                        text("UPDATE user_otps SET is_used = TRUE WHERE phone = :phone AND otp = :otp"),
                        {"phone": phone, "otp": otp}
                    )
                
                db.commit()
                return str(user_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return None
    
    @staticmethod
    def create_session(user_id: str, token_hash: str, expires_in_hours: int = 24) -> bool:
        """Create a new user session"""
        try:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
            
            db = next(get_db())
            
            db.execute(
                text("""
                    INSERT INTO user_sessions (user_id, token_hash, expires_at, created_at)
                    VALUES (:user_id, :token_hash, :expires_at, :created_at)
                """),
                {
                    "user_id": user_id,
                    "token_hash": token_hash,
                    "expires_at": expires_at,
                    "created_at": datetime.utcnow()
                }
            )
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False
    
    @staticmethod
    def validate_session(token_hash: str) -> Optional[str]:
        """Validate session and return user_id if valid"""
        try:
            db = next(get_db())
            
            result = db.execute(
                text("""
                    SELECT user_id FROM user_sessions 
                    WHERE token_hash = :token_hash AND expires_at > :now
                """),
                {"token_hash": token_hash, "now": datetime.utcnow()}
            ).fetchone()
            
            return str(result[0]) if result else None
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None
    
    @staticmethod
    def delete_session(token_hash: str) -> bool:
        """Delete a user session"""
        try:
            db = next(get_db())
            
            db.execute(
                text("DELETE FROM user_sessions WHERE token_hash = :token_hash"),
                {"token_hash": token_hash}
            )
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    @staticmethod
    def send_email_notification(user: Dict, message_type: str, **kwargs) -> bool:
        """Send email notification to user"""
        logger.info(f"Sending email notification to user", extra={
            "component": "user_service",
            "action": "send_email_notification",
            "user_id": user.get("user_id"),
            "message_type": message_type,
            "recipient": user.get("email")
        })
        
        try:
            # For now, just log the notification
            # In production, integrate with email service
            if message_type == "registration":
                subject = "Welcome to Pollinexus"
                message_body = f"Thank you for registering with our service. Your account has been created successfully."
            elif message_type == "login_otp":
                otp = kwargs.get("otp")
                subject = "Your Login OTP"
                message_body = f"Your OTP for login is: {otp}. It will expire in 5 minutes."
            elif message_type == "password_reset":
                otp = kwargs.get("otp")
                subject = "Password Reset OTP"
                message_body = f"Your password reset OTP is: {otp}. It will expire in 5 minutes."
            elif message_type == "account_verification":
                otp = kwargs.get("otp")
                subject = "Account Verification OTP"
                message_body = f"Your account verification OTP is: {otp}. It will expire in 5 minutes."
            else:
                subject = "Pollinexus Notification"
                message_body = kwargs.get("message", "You have a new notification from our service.")
            
            logger.info(f"Email notification prepared", extra={
                "component": "user_service",
                "action": "send_email_notification",
                "status": "prepared",
                "user_id": user.get("user_id"),
                "message_type": message_type,
                "subject": subject,
                "message_body": message_body
            })
            
            # TODO: Integrate with actual email service
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}", extra={
                "component": "user_service",
                "action": "send_email_notification",
                "status": "error",
                "user_id": user.get("user_id"),
                "message_type": message_type,
                "error": str(e)
            })
            return False
    
    @staticmethod
    def send_whatsapp_notification(user: Dict, message_type: str, **kwargs) -> bool:
        """Send WhatsApp notification to user"""
        logger.info(f"Sending WhatsApp notification to user", extra={
            "component": "user_service",
            "action": "send_whatsapp_notification",
            "user_id": user.get("user_id"),
            "message_type": message_type,
            "recipient": user.get("phone")
        })
        
        try:
            # For now, just log the notification
            # In production, integrate with WhatsApp service
            if message_type == "registration":
                message_body = f"Thank you for registering with our service. Your account has been created successfully."
            elif message_type == "login_otp":
                otp = kwargs.get("otp")
                message_body = f"Your OTP for login is: {otp}. It will expire in 5 minutes."
            elif message_type == "password_reset":
                otp = kwargs.get("otp")
                message_body = f"Your password reset OTP is: {otp}. It will expire in 5 minutes."
            elif message_type == "account_verification":
                otp = kwargs.get("otp")
                message_body = f"Your account verification OTP is: {otp}. It will expire in 5 minutes."
            else:
                message_body = kwargs.get("message", "You have a new notification from our service.")
            
            logger.info(f"WhatsApp notification prepared", extra={
                "component": "user_service",
                "action": "send_whatsapp_notification",
                "status": "prepared",
                "user_id": user.get("user_id"),
                "message_type": message_type,
                "message_body": message_body
            })
            
            # TODO: Integrate with actual WhatsApp service
            return True
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp notification: {e}", extra={
                "component": "user_service",
                "action": "send_whatsapp_notification",
                "status": "error",
                "user_id": user.get("user_id"),
                "message_type": message_type,
                "error": str(e)
            })
            return False 