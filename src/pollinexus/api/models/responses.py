"""
Pydantic response models for Pollinexus API.

This module contains all response models used for API output formatting.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Enumeration of job statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DatasetResponse(BaseModel):
    """Response model for dataset information."""
    
    id: int = Field(..., description="Dataset ID")
    name: str = Field(..., description="Dataset name")
    description: Optional[str] = Field(None, description="Dataset description")
    file_path: str = Field(..., description="Path to the dataset file")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    record_count: Optional[int] = Field(None, description="Number of records in dataset")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    """Response model for list of datasets."""
    
    datasets: List[DatasetResponse] = Field(..., description="List of datasets")
    total: int = Field(..., description="Total number of datasets")
    page: int = Field(1, description="Current page number")
    per_page: int = Field(10, description="Number of items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class AnalysisJobResponse(BaseModel):
    """Response model for analysis job information."""
    
    id: int = Field(..., description="Job ID")
    dataset_id: int = Field(..., description="Dataset ID")
    job_type: str = Field(..., description="Type of analysis job")
    status: JobStatus = Field(..., description="Job status")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Job parameters")
    results: Optional[Dict[str, Any]] = Field(None, description="Job results")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    celery_task_id: Optional[str] = Field(None, description="Celery task ID")
    
    class Config:
        from_attributes = True
        use_enum_values = True


class AnalysisJobListResponse(BaseModel):
    """Response model for list of analysis jobs."""
    
    jobs: List[AnalysisJobResponse] = Field(..., description="List of analysis jobs")
    total: int = Field(..., description="Total number of jobs")
    page: int = Field(1, description="Current page number")
    per_page: int = Field(10, description="Number of items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class PlantRecommendationResponse(BaseModel):
    """Response model for plant recommendation."""
    
    rank: int = Field(..., description="Recommendation rank")
    plant_species: str = Field(..., description="Plant species name")
    score: float = Field(..., description="Recommendation score")
    observation_count: int = Field(..., description="Number of observations")
    avg_bees_per_observation: float = Field(..., description="Average bees per observation")
    total_bees: int = Field(..., description="Total number of bees")
    native_bee_ratio: float = Field(..., description="Ratio of native bees")
    reasoning: str = Field(..., description="Explanation for recommendation")


class PlantRecommendationListResponse(BaseModel):
    """Response model for list of plant recommendations."""
    
    recommendations: List[PlantRecommendationResponse] = Field(..., description="List of recommendations")
    dataset_id: int = Field(..., description="Dataset ID")
    total_plants_analyzed: int = Field(..., description="Total number of plants analyzed")
    analysis_criteria: Dict[str, float] = Field(..., description="Analysis criteria weights")
    generated_at: datetime = Field(..., description="Generation timestamp")


class BeeAnalysisResponse(BaseModel):
    """Response model for bee analysis results."""
    
    bee_species: str = Field(..., description="Bee species name")
    observation_count: int = Field(..., description="Number of observations")
    avg_bees_per_observation: float = Field(..., description="Average bees per observation")
    total_bees: int = Field(..., description="Total number of bees")
    native_bee_ratio: float = Field(..., description="Ratio of native bees")


class BeeAnalysisListResponse(BaseModel):
    """Response model for list of bee analysis results."""
    
    bee_species_analysis: List[BeeAnalysisResponse] = Field(..., description="Bee species analysis")
    plant_species_analysis: List[Dict[str, Any]] = Field(..., description="Plant species analysis")
    seasonal_analysis: List[Dict[str, Any]] = Field(..., description="Seasonal analysis")
    site_analysis: List[Dict[str, Any]] = Field(..., description="Site analysis")
    summary: Dict[str, Any] = Field(..., description="Analysis summary")


class VisualizationResponse(BaseModel):
    """Response model for visualization."""
    
    id: int = Field(..., description="Visualization ID")
    dataset_id: int = Field(..., description="Dataset ID")
    plot_type: str = Field(..., description="Type of plot")
    plot_data: Dict[str, Any] = Field(..., description="Plot data")
    plot_config: Optional[Dict[str, Any]] = Field(None, description="Plot configuration")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class ExportResponse(BaseModel):
    """Response model for data export."""
    
    dataset_id: int = Field(..., description="Dataset ID")
    format: str = Field(..., description="Export format")
    file_path: str = Field(..., description="Path to exported file")
    file_size: int = Field(..., description="File size in bytes")
    record_count: int = Field(..., description="Number of exported records")
    exported_at: datetime = Field(..., description="Export timestamp")


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str = Field(..., description="Service status")
    timestamp: float = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")
    database_status: str = Field(..., description="Database status")
    celery_status: str = Field(..., description="Celery status")


class ErrorResponse(BaseModel):
    """Response model for error messages."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class SuccessResponse(BaseModel):
    """Response model for success messages."""
    
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(..., description="Response timestamp")


class PaginationResponse(BaseModel):
    """Response model for pagination metadata."""
    
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of items per page")
    total: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")
    next_page: Optional[int] = Field(None, description="Next page number")
    prev_page: Optional[int] = Field(None, description="Previous page number") 