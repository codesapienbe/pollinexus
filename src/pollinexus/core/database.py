"""
Database configuration and utilities for Pollinexus.

This module provides database connection management, session handling,
and migration utilities for the Pollinexus application.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
from typing import Optional, Generator
import logging

from .config import settings
from .logging import logger
from .security import calculate_file_checksum

# Import Base from models
from ..models.database import Base

# Database URL
DATABASE_URL = settings.database_url

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=settings.debug
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Run migrations
        run_migrations()
        
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def run_migrations():
    """Run database migrations."""
    try:
        # Check if file_checksum column exists
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(datasets)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'file_checksum' not in columns:
                logger.info("Adding file_checksum column to datasets table")
                
                # Add the column
                conn.execute(text("ALTER TABLE datasets ADD COLUMN file_checksum VARCHAR(64)"))
                
                # Create index for the new column
                conn.execute(text("CREATE INDEX idx_datasets_checksum ON datasets(file_checksum)"))
                
                # Calculate checksums for existing files
                result = conn.execute(text("SELECT id, file_path FROM datasets WHERE file_checksum IS NULL"))
                existing_datasets = result.fetchall()
                
                for dataset_id, file_path in existing_datasets:
                    try:
                        if os.path.exists(file_path):
                            checksum = calculate_file_checksum(file_path)
                            conn.execute(
                                text("UPDATE datasets SET file_checksum = :checksum WHERE id = :id"),
                                {"checksum": checksum, "id": dataset_id}
                            )
                            logger.info(f"Calculated checksum for dataset {dataset_id}: {checksum}")
                        else:
                            logger.warning(f"File not found for dataset {dataset_id}: {file_path}")
                            # Set a placeholder checksum for missing files
                            conn.execute(
                                text("UPDATE datasets SET file_checksum = 'FILE_NOT_FOUND' WHERE id = :id"),
                                {"id": dataset_id}
                            )
                    except Exception as e:
                        logger.error(f"Failed to calculate checksum for dataset {dataset_id}: {e}")
                        # Set error checksum
                        conn.execute(
                            text("UPDATE datasets SET file_checksum = 'CALCULATION_ERROR' WHERE id = :id"),
                            {"id": dataset_id}
                        )
                
                conn.commit()
                logger.info("Migration completed successfully")
            else:
                logger.info("file_checksum column already exists")
                
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


def check_database_connection() -> bool:
    """Check if database connection is working."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def get_database_info() -> dict:
    """Get database information."""
    try:
        with engine.connect() as conn:
            # Get database version
            if "sqlite" in DATABASE_URL:
                result = conn.execute(text("SELECT sqlite_version()"))
                version_row = result.fetchone()
                version = version_row[0] if version_row else "unknown"
            else:
                result = conn.execute(text("SELECT version()"))
                version_row = result.fetchone()
                version = version_row[0] if version_row else "unknown"
            
            # Get table count
            result = conn.execute(text("SELECT COUNT(*) FROM datasets"))
            dataset_row = result.fetchone()
            dataset_count = dataset_row[0] if dataset_row else 0
            
            result = conn.execute(text("SELECT COUNT(*) FROM analysis_jobs"))
            job_row = result.fetchone()
            job_count = job_row[0] if job_row else 0
            
            return {
                "database_type": "sqlite" if "sqlite" in DATABASE_URL else "postgresql",
                "version": version,
                "dataset_count": dataset_count,
                "job_count": job_count,
                "connection_status": "connected"
            }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {
            "database_type": "unknown",
            "version": "unknown",
            "dataset_count": 0,
            "job_count": 0,
            "connection_status": "error",
            "error": str(e)
        }


def close_database_connections():
    """Close all database connections gracefully."""
    try:
        logger.info("Closing database connections...")
        
        # Close all sessions
        SessionLocal.close_all()
        
        # Dispose of the engine
        engine.dispose()
        
        logger.info("Database connections closed successfully")
        
    except Exception as e:
        logger.error(f"Failed to close database connections: {e}")
        raise 