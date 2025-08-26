"""
User API request and response models for Pollinexus API.

This module defines Pydantic models for user-related API endpoints
including registration, authentication, and user management.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserRegistration(BaseModel):
    """User registration request model."""
    
    full_name: str = Field(..., min_length=1, max_length=255, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    phone: str = Field(..., min_length=10, max_length=25, description="User's phone number")


class UserLoginRequest(BaseModel):
    """User login request model."""
    
    email: EmailStr = Field(..., description="User's email address")


class VerifyOTPRequest(BaseModel):
    """OTP verification request model."""
    
    email: Optional[EmailStr] = Field(None, description="User's email address")
    phone: Optional[str] = Field(None, min_length=10, max_length=25, description="User's phone number")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")


class VerificationRequest(BaseModel):
    """Verification request model."""
    
    email: Optional[EmailStr] = Field(None, description="User's email address")
    phone: Optional[str] = Field(None, min_length=10, max_length=25, description="User's phone number")
    verification_type: str = Field(..., description="Type of verification: 'email' or 'whatsapp'")


class UserResponse(BaseModel):
    """Basic user response model."""
    
    user_id: str = Field(..., description="User's unique identifier")
    full_name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    phone: str = Field(..., description="User's phone number")
    is_verified: bool = Field(..., description="Whether the user is verified")
    role: str = Field(..., description="User's role")


class UserResponseWithId(BaseModel):
    """User response model with ID for registration."""
    
    user_id: str = Field(..., description="User's unique identifier")
    full_name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    phone: str = Field(..., description="User's phone number")
    role: str = Field(..., description="User's role")
    message: str = Field(..., description="Response message")


class UserResponseWithFaces(BaseModel):
    """User response model with face reference IDs."""
    
    user_id: str = Field(..., description="User's unique identifier")
    full_name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    phone: str = Field(..., description="User's phone number")
    faces: List[str] = Field(default=[], description="List of face reference IDs")


class TokenResponse(BaseModel):
    """Authentication token response model."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")


class VerificationResponse(BaseModel):
    """Verification response model."""
    
    message: str = Field(..., description="Response message")
    expires_in: int = Field(..., description="OTP expiration time in seconds")
    verification_type: str = Field(..., description="Type of verification used")


class AddFaceResponse(BaseModel):
    """Add face response model."""
    
    user_id: str = Field(..., description="User's unique identifier")
    face_id: str = Field(..., description="Face reference ID")
    face_url: str = Field(..., description="URL to access the face image")
    message: str = Field(..., description="Response message")


class UserListResponse(BaseModel):
    """User list response model."""
    
    users: List[dict] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of users per page")


class LoginResponse(BaseModel):
    """Login response model."""
    
    message: str = Field(..., description="Response message")
    expires_in: int = Field(..., description="OTP expiration time in seconds") 