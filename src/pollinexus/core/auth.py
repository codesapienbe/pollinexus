"""
Authentication utilities for Pollinexus API.

This module provides authentication and authorization functionality
including JWT token handling and user session management.
"""

import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..core.config import settings
from ..core.logging import logger
from ..services.user_service import UserService

# Security scheme
security = HTTPBearer()

# JWT Configuration
JWT_SECRET = "your-secret-key-here"  # In production, use environment variable
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60 * 24  # 24 hours
OTP_EXPIRATION_MINUTES = 5
OTP_LENGTH = 6


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.JWTError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def hash_token(token: str) -> str:
    """Hash a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    
    # Verify JWT token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = UserService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user["is_deleted"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account has been deleted",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    """Get current active user (verified)."""
    if not current_user["is_verified"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account not verified"
        )
    return current_user


async def get_current_admin_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    """Get current admin user."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def verify_otp_and_generate_token(request, mark_verified: bool = False) -> Dict:
    """Verify OTP and generate access token."""
    try:
        # Verify OTP
        user_id = UserService.verify_otp(
            email=request.email,
            phone=request.phone,
            otp=request.otp
        )
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        # Get user
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user["is_deleted"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account has been deleted"
            )
        
        # Mark user as verified if requested
        if mark_verified and not user["is_verified"]:
            UserService.update_user(user_id, is_verified=True)
            user["is_verified"] = True
        
        # Generate access token
        token_data = {
            "sub": user_id,
            "email": user["email"],
            "role": user["role"]
        }
        
        access_token = create_access_token(token_data)
        
        # Create session
        token_hash = hash_token(access_token)
        UserService.create_session(user_id, token_hash)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": JWT_EXPIRATION_MINUTES * 60,
            "user": {
                "user_id": user["user_id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "phone": user["phone"],
                "is_verified": user["is_verified"],
                "role": user["role"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in verify_otp_and_generate_token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 