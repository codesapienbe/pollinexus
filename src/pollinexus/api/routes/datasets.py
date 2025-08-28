"""
Dataset management routes for Pollinexus API.

This module contains all endpoints related to dataset operations
with comprehensive logging and monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os
from pathlib import Path as PathLib
import time

from ...core.database import get_db
from ...services.database_service import DatabaseService
from ...services.data_service import DataService
from ...core.logging import logger, request_id, correlation_id
from ...core.metrics import monitor_performance
from ...core.error_tracking import track_errors, error_tracker
from ...core.security import calculate_upload_checksum
from ..models.requests import DatasetCreate, DatasetUpdate, SearchRequest, FilterRequest
from ..models.responses import DatasetResponse, DatasetListResponse, SuccessResponse, ErrorResponse

router = APIRouter()


@router.post("/datasets/", response_model=DatasetResponse, tags=["🔧 Setup, Data Loading, and System Monitoring"])
@monitor_performance("api_dataset_create")
@track_errors("api_dataset_upload")
async def create_dataset(
    file: UploadFile = File(..., description="Dataset file (CSV, Excel, Parquet)"),
    db: Session = Depends(get_db)
):
    """Upload and create a new dataset with comprehensive logging and duplicate detection."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Dataset upload request received",
        extra={
            "request_id": req_id,
            "correlation_id": corr_id,
            "file_name": getattr(file, "filename", None),
            "file_size": getattr(file, "size", None),
            "operation": "api_dataset_upload"
        }
    )
    
    start_time = time.time()
    
    try:
        # Validate file type
        allowed_extensions = ['.csv', '.xlsx', '.xls', '.parquet']
        provided_filename = getattr(file, "filename", None) or "dataset.csv"
        file_extension = PathLib(provided_filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            logger.warning(
                "Invalid file type attempted",
                extra={
                    "request_id": req_id,
                    "correlation_id": corr_id,
                    "file_name": provided_filename,
                    "file_extension": file_extension,
                    "allowed_extensions": allowed_extensions,
                    "operation": "api_dataset_upload"
                }
            )
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Calculate file checksum for duplicate detection
        logger.info(
            "Calculating file checksum",
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "file_name": provided_filename,
                "operation": "api_dataset_upload"
            }
        )
        
        try:
            file_checksum = calculate_upload_checksum(file)
            logger.info(
                "File checksum calculated successfully",
                extra={
                    "request_id": req_id,
                    "correlation_id": corr_id,
                    "file_checksum": file_checksum,
                    "operation": "api_dataset_upload"
                }
            )
        except Exception as e:
            logger.error(
                "Failed to calculate file checksum",
                extra={
                    "request_id": req_id,
                    "correlation_id": corr_id,
                    "file_name": provided_filename,
                    "error": str(e),
                    "operation": "api_dataset_upload"
                }
            )
            raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")
        
        # Check for duplicate file by checksum
        db_service = DatabaseService(db)
        existing_dataset = db_service.get_dataset_by_checksum(file_checksum)
        if existing_dataset:
            logger.warning(
                "Duplicate file upload attempted",
                extra={
                    "request_id": req_id,
                    "correlation_id": corr_id,
                    "file_checksum": file_checksum,
                    "existing_dataset_id": existing_dataset.id,
                    "existing_dataset_name": existing_dataset.name,
                    "operation": "api_dataset_upload"
                }
            )
            raise HTTPException(
                status_code=409,
                detail=f"File already exists as dataset '{existing_dataset.name}' (ID: {existing_dataset.id})"
            )
        
        # Create upload directory
        upload_dir = PathLib("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        timestamp = int(time.time())
        sanitized_original = provided_filename.replace(' ', '_')
        safe_filename = f"{timestamp}_{sanitized_original}"
        file_path = upload_dir / safe_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.debug(
            "File saved successfully",
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "file_path": str(file_path),
                "operation": "api_dataset_upload"
            }
        )
        
        # Validate dataset
        data_service = DataService()
        try:
            data = data_service.load_dataset(str(file_path))
            validation = data_service.validate_dataset(data)
            
            logger.info(
                "Dataset validation completed",
                extra={
                    "request_id": req_id,
                    "correlation_id": corr_id,
                    "validation_result": validation['is_valid'],
                    "errors_count": len(validation['errors']),
                    "warnings_count": len(validation['warnings']),
                    "operation": "api_dataset_upload"
                }
            )
            
            if not validation['is_valid']:
                os.remove(file_path)
                raise HTTPException(
                    status_code=400, 
                    detail=f"Dataset validation failed: {validation['errors']}"
                )
                
        except Exception as e:
            if file_path.exists():
                os.remove(file_path)
            logger.error(
                "Dataset validation failed",
                extra={
                    "request_id": req_id,
                    "correlation_id": corr_id,
                    "error": str(e),
                    "operation": "api_dataset_upload"
                }
            )
            raise HTTPException(status_code=400, detail=f"Error loading dataset: {str(e)}")
        
        # Create dataset record with checksum
        dataset_name = PathLib(provided_filename).stem or f"dataset_{timestamp}"
        dataset_create = DatasetCreate(
            name=dataset_name,
            description=None,
            file_path=str(file_path),
            file_checksum=file_checksum
        )
        
        try:
            dataset = db_service.create_dataset(dataset_create)
        except ValueError as e:
            # Handle duplicate detection error from database service
            if file_path.exists():
                os.remove(file_path)
            raise HTTPException(status_code=409, detail=str(e))
        
        operation_time = time.time() - start_time
        
        logger.info(
            "Dataset created successfully via API",
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "dataset_id": dataset.id,
                "dataset_name": dataset_name,
                "file_checksum": file_checksum,
                "operation_time": operation_time,
                "operation": "api_dataset_upload"
            }
        )
        
        return dataset
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Unexpected error in dataset upload",
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "error": str(e),
                "operation": "api_dataset_upload"
            }
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@monitor_performance("api_dataset_list")
@track_errors("api_dataset_list")
@router.get("/datasets/", response_model=DatasetListResponse, tags=["📊 Exploratory Data Analysis (EDA)"])
async def list_datasets(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search term for dataset name or description"),
    db: Session = Depends(get_db)
):
    """List datasets with pagination and search."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Dataset list request received",
        request_id=req_id,
        correlation_id=corr_id,
        skip=skip,
        limit=limit,
        search=search,
        operation="api_dataset_list"
    )
    
    try:
        db_service = DatabaseService(db)
        datasets = db_service.list_datasets(skip=skip, limit=limit, search=search)
        
        # Get total count for pagination
        total_datasets = db_service.list_datasets(skip=0, limit=1000, search=search)
        total_count = len(total_datasets)
        
        # Calculate pagination info
        has_next = (skip + limit) < total_count
        has_prev = skip > 0
        
        response = DatasetListResponse(
            datasets=datasets,
            total=total_count,
            page=(skip // limit) + 1,
            per_page=limit,
            has_next=has_next,
            has_prev=has_prev
        )
        
        logger.info(
            "Dataset list retrieved successfully",
            request_id=req_id,
            correlation_id=corr_id,
            total_datasets=total_count,
            returned_datasets=len(datasets),
            operation="api_dataset_list"
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Dataset list retrieval failed",
            request_id=req_id,
            correlation_id=corr_id,
            error=str(e),
            operation="api_dataset_list"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@monitor_performance("api_dataset_get")
@track_errors("api_dataset_get")
@router.get("/datasets/{dataset_id}", response_model=DatasetResponse, tags=["📊 Exploratory Data Analysis (EDA)"])
async def get_dataset(
    dataset_id: int = Path(..., description="Dataset ID"),
    db: Session = Depends(get_db)
):
    """Get dataset by ID with detailed information."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Dataset get request received",
        request_id=req_id,
        correlation_id=corr_id,
        dataset_id=dataset_id,
        operation="api_dataset_get"
    )
    
    try:
        db_service = DatabaseService(db)
        dataset = db_service.get_dataset(dataset_id)
        
        if not dataset:
            logger.warning(
                "Dataset not found",
                request_id=req_id,
                correlation_id=corr_id,
                dataset_id=dataset_id,
                operation="api_dataset_get"
            )
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        logger.info(
            "Dataset retrieved successfully",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            dataset_name=dataset.name,
            operation="api_dataset_get"
        )
        
        return dataset
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Dataset retrieval failed",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            error=str(e),
            operation="api_dataset_get"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/datasets/{dataset_id}", response_model=DatasetResponse, tags=["🧹 Data Cleaning and Preprocessing"])
@monitor_performance("api_dataset_update")
@track_errors("api_dataset_update")
async def update_dataset(
    dataset_id: int = Path(..., description="Dataset ID"),
    dataset_update: DatasetUpdate = None,
    db: Session = Depends(get_db)
):
    """Update dataset information."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Dataset update request received",
        request_id=req_id,
        correlation_id=corr_id,
        dataset_id=dataset_id,
        update_fields=list(dataset_update.dict(exclude_unset=True).keys()) if dataset_update else [],
        operation="api_dataset_update"
    )
    
    try:
        db_service = DatabaseService(db)
        
        # Check if dataset exists
        existing_dataset = db_service.get_dataset(dataset_id)
        if not existing_dataset:
            logger.warning(
                "Dataset not found for update",
                request_id=req_id,
                correlation_id=corr_id,
                dataset_id=dataset_id,
                operation="api_dataset_update"
            )
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Update dataset
        updated_dataset = db_service.update_dataset(dataset_id, dataset_update)
        
        logger.info(
            "Dataset updated successfully",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            update_fields=list(dataset_update.dict(exclude_unset=True).keys()) if dataset_update else [],
            operation="api_dataset_update"
        )
        
        return updated_dataset
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Dataset update failed",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            error=str(e),
            operation="api_dataset_update"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/datasets/{dataset_id}", tags=["🧹 Data Cleaning and Preprocessing"])
@monitor_performance("api_dataset_delete")
@track_errors("api_dataset_delete")
async def delete_dataset(
    dataset_id: int = Path(..., description="Dataset ID"),
    db: Session = Depends(get_db)
):
    """Delete dataset and associated files."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Dataset delete request received",
        request_id=req_id,
        correlation_id=corr_id,
        dataset_id=dataset_id,
        operation="api_dataset_delete"
    )
    
    try:
        db_service = DatabaseService(db)
        
        # Get dataset to check if it exists and get file path
        dataset = db_service.get_dataset(dataset_id)
        if not dataset:
            logger.warning(
                "Dataset not found for deletion",
                request_id=req_id,
                correlation_id=corr_id,
                dataset_id=dataset_id,
                operation="api_dataset_delete"
            )
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Remove file if it exists
        if os.path.exists(dataset.file_path):
            try:
                os.remove(dataset.file_path)
                logger.debug(
                    "Dataset file removed",
                    request_id=req_id,
                    correlation_id=corr_id,
                    file_path=dataset.file_path,
                    operation="api_dataset_delete"
                )
            except Exception as e:
                logger.warning(
                    "Failed to remove dataset file",
                    request_id=req_id,
                    correlation_id=corr_id,
                    file_path=dataset.file_path,
                    error=str(e),
                    operation="api_dataset_delete"
                )
        
        # Remove from database
        success = db_service.delete_dataset(dataset_id)
        
        if success:
            logger.info(
                "Dataset deleted successfully",
                request_id=req_id,
                correlation_id=corr_id,
                dataset_id=dataset_id,
                dataset_name=dataset.name,
                operation="api_dataset_delete"
            )
            return SuccessResponse(message="Dataset deleted successfully")
        else:
            logger.error(
                "Failed to delete dataset from database",
                request_id=req_id,
                correlation_id=corr_id,
                dataset_id=dataset_id,
                operation="api_dataset_delete"
            )
            raise HTTPException(status_code=500, detail="Failed to delete dataset")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Dataset deletion failed",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            error=str(e),
            operation="api_dataset_delete"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/datasets/{dataset_id}/info", tags=["🔍 Data Quality Assessment"])
@monitor_performance("api_dataset_info")
@track_errors("api_dataset_info")
async def get_dataset_info(
    dataset_id: int = Path(..., description="Dataset ID"),
    db: Session = Depends(get_db)
):
    """Get detailed dataset information and statistics."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Dataset info request received",
        request_id=req_id,
        correlation_id=corr_id,
        dataset_id=dataset_id,
        operation="api_dataset_info"
    )
    
    try:
        db_service = DatabaseService(db)
        dataset = db_service.get_dataset(dataset_id)
        
        if not dataset:
            logger.warning(
                "Dataset not found for info request",
                request_id=req_id,
                correlation_id=corr_id,
                dataset_id=dataset_id,
                operation="api_dataset_info"
            )
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Get dataset statistics
        data_service = DataService()
        data = data_service.load_dataset(dataset.file_path)
        dataset_info = data_service.get_dataset_info(data)
        
        # Combine dataset and statistics
        response = {
            "dataset": dataset,
            "statistics": dataset_info,
            "file_info": {
                "file_path": dataset.file_path,
                "file_size_mb": dataset_info.get('memory_usage_mb', 0),
                "file_exists": os.path.exists(dataset.file_path)
            }
        }
        
        logger.info(
            "Dataset info retrieved successfully",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            total_records=dataset_info.get('total_records', 0),
            total_columns=dataset_info.get('total_columns', 0),
            operation="api_dataset_info"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Dataset info retrieval failed",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            error=str(e),
            operation="api_dataset_info"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/datasets/search", tags=["📊 Exploratory Data Analysis (EDA)"])
@monitor_performance("api_dataset_search")
@track_errors("api_dataset_search")
async def search_datasets(
    search_request: SearchRequest,
    db: Session = Depends(get_db)
):
    """Search datasets by name, description, or content."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Dataset search request received",
        request_id=req_id,
        correlation_id=corr_id,
        query=search_request.query,
        limit=search_request.limit,
        offset=search_request.offset,
        operation="api_dataset_search"
    )
    
    try:
        db_service = DatabaseService(db)
        
        # Simple search implementation - can be enhanced with full-text search
        datasets = db_service.list_datasets(
            skip=search_request.offset,
            limit=search_request.limit,
            search=search_request.query
        )
        
        # Get total count for pagination
        total_datasets = db_service.list_datasets(skip=0, limit=1000, search=search_request.query)
        total_count = len(total_datasets)
        
        response = {
            "query": search_request.query,
            "results": datasets,
            "total": total_count,
            "limit": search_request.limit,
            "offset": search_request.offset,
            "has_more": (search_request.offset + search_request.limit) < total_count
        }
        
        logger.info(
            "Dataset search completed successfully",
            request_id=req_id,
            correlation_id=corr_id,
            query=search_request.query,
            results_count=len(datasets),
            total_count=total_count,
            operation="api_dataset_search"
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Dataset search failed",
            request_id=req_id,
            correlation_id=corr_id,
            query=search_request.query,
            error=str(e),
            operation="api_dataset_search"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/datasets/{dataset_id}/health", tags=["🔍 Data Quality Assessment"])
@monitor_performance("api_dataset_health")
@track_errors("api_dataset_health")
async def get_dataset_health(
    dataset_id: int = Path(..., description="Dataset ID"),
    db: Session = Depends(get_db)
):
    """Get dataset health and validation status."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Dataset health check request received",
        request_id=req_id,
        correlation_id=corr_id,
        dataset_id=dataset_id,
        operation="api_dataset_health"
    )
    
    try:
        db_service = DatabaseService(db)
        dataset = db_service.get_dataset(dataset_id)
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Check file existence and accessibility
        file_exists = os.path.exists(dataset.file_path)
        file_readable = False
        file_size = 0
        
        if file_exists:
            try:
                file_size = os.path.getsize(dataset.file_path)
                # Try to read a small portion to check accessibility
                with open(dataset.file_path, 'r') as f:
                    f.read(1024)  # Read first 1KB
                file_readable = True
            except Exception as e:
                logger.warning(
                    "Dataset file not readable",
                    request_id=req_id,
                    correlation_id=corr_id,
                    dataset_id=dataset_id,
                    file_path=dataset.file_path,
                    error=str(e),
                    operation="api_dataset_health"
                )
        
        # Validate dataset if file is accessible
        validation_status = "unknown"
        validation_details = {}
        
        if file_readable:
            try:
                data_service = DataService()
                data = data_service.load_dataset(dataset.file_path)
                validation = data_service.validate_dataset(data)
                validation_status = "valid" if validation['is_valid'] else "invalid"
                validation_details = validation
            except Exception as e:
                validation_status = "error"
                validation_details = {"error": str(e)}
        
        health_status = "healthy" if file_exists and file_readable and validation_status == "valid" else "unhealthy"
        
        response = {
            "dataset_id": dataset_id,
            "health_status": health_status,
            "file_status": {
                "exists": file_exists,
                "readable": file_readable,
                "size_bytes": file_size,
                "size_mb": file_size / (1024 * 1024) if file_size > 0 else 0
            },
            "validation_status": validation_status,
            "validation_details": validation_details,
            "last_checked": time.time()
        }
        
        logger.info(
            "Dataset health check completed",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            health_status=health_status,
            file_exists=file_exists,
            file_readable=file_readable,
            validation_status=validation_status,
            operation="api_dataset_health"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Dataset health check failed",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            error=str(e),
            operation="api_dataset_health"
        )
        raise HTTPException(status_code=500, detail="Internal server error") 