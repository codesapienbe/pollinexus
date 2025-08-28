"""
User database models for Pollinexus API.

This module defines the database models for user management,
authentication, and authorization using DuckDB.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from datetime import datetime

from .database import Base


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(25), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    role = Column(String(50), default="user", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class UserOTP(Base):
    """User OTP model for authentication."""
    
    __tablename__ = "user_otps"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(25), nullable=True)
    otp = Column(String(10), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class UserSession(Base):
    """User session model for authentication."""
    
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False) 