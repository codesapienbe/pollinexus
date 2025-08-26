"""
Database models for Pollinexus.

This module contains SQLAlchemy models for the application database.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import duckdb

Base = declarative_base()


class Dataset(Base):
    """Dataset model for storing uploaded pollinator data files."""
    
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # File size in bytes
    record_count = Column(Integer)  # Number of records in dataset
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analysis_jobs = relationship("AnalysisJob", back_populates="dataset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Dataset(id={self.id}, name='{self.name}')>"


class AnalysisJob(Base):
    """Analysis job model for tracking background analysis tasks."""
    
    __tablename__ = "analysis_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False, index=True)
    job_type = Column(String(100), nullable=False, index=True)  # e.g., 'bee_preferences', 'plant_recommendations'
    status = Column(String(50), default="pending", index=True)  # pending, running, completed, failed
    parameters = Column(JSON)  # Job parameters as JSON
    results = Column(JSON)  # Job results as JSON
    error_message = Column(Text)  # Error message if job failed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)  # When job started processing
    completed_at = Column(DateTime, index=True)  # When job completed
    celery_task_id = Column(String(255), index=True)  # Celery task ID
    
    # Relationships
    dataset = relationship("Dataset", back_populates="analysis_jobs")
    recommendations = relationship("PlantRecommendation", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AnalysisJob(id={self.id}, type='{self.job_type}', status='{self.status}')>"


class PlantRecommendation(Base):
    """Plant recommendation model for storing analysis results."""
    
    __tablename__ = "plant_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=False, index=True)
    plant_species = Column(String(255), nullable=False, index=True)
    score = Column(Numeric(10, 3))  # Recommendation score
    rank = Column(Integer)  # Ranking position
    reasoning = Column(Text)  # Explanation for recommendation
    bee_count = Column(Integer)  # Number of bees observed
    avg_bees = Column(Numeric(10, 2))  # Average bees per observation
    native_bee_ratio = Column(Numeric(5, 3))  # Ratio of native bees
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("AnalysisJob", back_populates="recommendations")
    
    def __repr__(self):
        return f"<PlantRecommendation(id={self.id}, plant='{self.plant_species}', score={self.score})>"


class AnalysisResult(Base):
    """Analysis result model for storing detailed analysis outputs."""
    
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=False, index=True)
    result_type = Column(String(100), nullable=False)  # e.g., 'model_accuracy', 'feature_importance'
    result_data = Column(JSON)  # Result data as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, type='{self.result_type}')>" 