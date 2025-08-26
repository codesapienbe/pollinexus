"""
Pydantic request models for Pollinexus API.

This module contains all request models used for API input validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class JobType(str, Enum):
    """Enumeration of supported analysis job types."""
    BEE_PREFERENCES = "bee_preferences"
    PLANT_RECOMMENDATIONS = "plant_recommendations"
    SEASONAL_ANALYSIS = "seasonal_analysis"
    SITE_COMPARISON = "site_comparison"
    VISUALIZATION = "visualization"


class PlotType(str, Enum):
    """Enumeration of supported plot types."""
    BEE_DISTRIBUTION = "bee_distribution"
    PLANT_DISTRIBUTION = "plant_distribution"
    SEASONAL_PATTERNS = "seasonal_patterns"
    SITE_COMPARISON = "site_comparison"
    INTERACTIVE_DASHBOARD = "interactive_dashboard"


class DatasetCreate(BaseModel):
    """Request model for creating a new dataset."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Dataset name")
    description: Optional[str] = Field(None, max_length=1000, description="Dataset description")
    file_path: str = Field(..., description="Path to the dataset file")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class DatasetUpdate(BaseModel):
    """Request model for updating a dataset."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Dataset name")
    description: Optional[str] = Field(None, max_length=1000, description="Dataset description")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v


class AnalysisJobCreate(BaseModel):
    """Request model for creating a new analysis job."""
    
    dataset_id: int = Field(..., gt=0, description="ID of the dataset to analyze")
    job_type: JobType = Field(..., description="Type of analysis to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Analysis parameters")
    
    class Config:
        use_enum_values = True


class AnalysisJobUpdate(BaseModel):
    """Request model for updating an analysis job."""
    
    status: Optional[str] = Field(None, description="Job status")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Analysis parameters")
    results: Optional[Dict[str, Any]] = Field(None, description="Analysis results")


class VisualizationRequest(BaseModel):
    """Request model for creating visualizations."""
    
    dataset_id: int = Field(..., gt=0, description="ID of the dataset to visualize")
    plot_types: List[PlotType] = Field(..., min_items=1, description="Types of plots to create")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Visualization parameters")
    
    class Config:
        use_enum_values = True


class PlantRecommendationRequest(BaseModel):
    """Request model for plant recommendation analysis."""
    
    dataset_id: int = Field(..., gt=0, description="ID of the dataset to analyze")
    top_n: int = Field(3, ge=1, le=50, description="Number of top recommendations to return")
    criteria: Optional[str] = Field("native_bee_support", description="Recommendation criteria")
    
    @validator('criteria')
    def validate_criteria(cls, v):
        valid_criteria = ['native_bee_support', 'diversity', 'seasonal_coverage', 'abundance']
        if v and v not in valid_criteria:
            raise ValueError(f'Criteria must be one of: {valid_criteria}')
        return v


class BeePreferenceRequest(BaseModel):
    """Request model for bee preference analysis."""
    
    dataset_id: int = Field(..., gt=0, description="ID of the dataset to analyze")
    target_column: str = Field("nonnative_bee", description="Target column for analysis")
    model_type: Optional[str] = Field("random_forest", description="Machine learning model type")
    test_size: float = Field(0.2, ge=0.1, le=0.5, description="Test set size ratio")
    
    @validator('model_type')
    def validate_model_type(cls, v):
        valid_models = ['random_forest', 'logistic_regression', 'svm', 'neural_network']
        if v and v not in valid_models:
            raise ValueError(f'Model type must be one of: {valid_models}')
        return v


class ExportRequest(BaseModel):
    """Request model for exporting data."""
    
    dataset_id: int = Field(..., gt=0, description="ID of the dataset to export")
    format: str = Field("csv", description="Export format")
    query: Optional[str] = Field(None, description="Custom SQL query for export")
    
    @validator('format')
    def validate_format(cls, v):
        valid_formats = ['csv', 'json', 'parquet', 'excel']
        if v not in valid_formats:
            raise ValueError(f'Format must be one of: {valid_formats}')
        return v


class SearchRequest(BaseModel):
    """Request model for searching datasets."""
    
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class FilterRequest(BaseModel):
    """Request model for filtering datasets."""
    
    bee_species: Optional[str] = Field(None, description="Filter by bee species")
    plant_species: Optional[str] = Field(None, description="Filter by plant species")
    season: Optional[str] = Field(None, description="Filter by season")
    site: Optional[str] = Field(None, description="Filter by site")
    min_bees: Optional[int] = Field(None, ge=0, description="Minimum number of bees")
    max_bees: Optional[int] = Field(None, ge=0, description="Maximum number of bees")
    native_only: Optional[bool] = Field(None, description="Filter for native bees only") 