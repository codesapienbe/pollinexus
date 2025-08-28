"""
Analysis routes for Pollinexus API.

This module contains all endpoints related to data analysis operations
with comprehensive logging and monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import time
from datetime import datetime

from ...core.database import get_db
from ...services.database_service import DatabaseService
from ...tasks.celery_app import celery_app, get_task_status, cancel_task
from ...tasks.analysis import (
    analyze_bee_preferences,
    generate_plant_recommendations,
    seasonal_analysis,
    site_comparison
)
from ...core.logging import logger, request_id, correlation_id, get_monitoring_metrics, reset_monitoring_metrics
from ...core.metrics import monitor_performance
from ...core.error_tracking import track_errors, error_tracker
from ..models.requests import (
    AnalysisJobCreate,
    AnalysisJobUpdate,
    PlantRecommendationRequest,
    BeePreferenceRequest
)
from ..models.responses import (
    AnalysisJobResponse,
    AnalysisJobListResponse,
    PlantRecommendationListResponse,
    BeeAnalysisListResponse,
    SuccessResponse,
    ErrorResponse
)

router = APIRouter()


@router.get("/monitoring/metrics/", response_model=Dict[str, Any])
@monitor_performance("api_monitoring_metrics")
async def get_logging_metrics():
    """Get comprehensive logging and monitoring metrics."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Monitoring metrics request received",
        extra={
            "request_id": req_id,
            "correlation_id": corr_id,
            "operation": "api_monitoring_metrics"
        }
    )
    
    try:
        metrics = get_monitoring_metrics()
        
        # Add additional system metrics
        import psutil
        system_metrics = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "active_connections": len(psutil.net_connections()),
            "process_count": len(psutil.pids())
        }
        
        response_data = {
            "timestamp": time.time(),
            "request_id": req_id,
            "correlation_id": corr_id,
            "logging_metrics": metrics,
            "system_metrics": system_metrics
        }
        
        logger.info(
            "Monitoring metrics retrieved successfully",
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "metrics_count": len(metrics),
                "operation": "api_monitoring_metrics"
            }
        )
        
        return response_data
        
    except Exception as e:
        logger.error(
            "Failed to retrieve monitoring metrics",
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "error": str(e),
                "operation": "api_monitoring_metrics"
            }
        )
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")


@router.post("/monitoring/metrics/reset/", response_model=SuccessResponse)
@monitor_performance("api_monitoring_reset")
async def reset_metrics():
    """Reset monitoring metrics (useful for testing or periodic resets)."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Monitoring metrics reset request received",
        extra={
            "request_id": req_id,
            "correlation_id": corr_id,
            "operation": "api_monitoring_reset"
        }
    )
    
    try:
        reset_monitoring_metrics()
        
        logger.info(
            "Monitoring metrics reset successfully",
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "operation": "api_monitoring_reset"
            }
        )
        
        return SuccessResponse(
            message="Monitoring metrics reset successfully",
            data={"request_id": req_id, "correlation_id": corr_id},
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(
            "Failed to reset monitoring metrics",
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "error": str(e),
                "operation": "api_monitoring_reset"
            }
        )
        raise HTTPException(status_code=500, detail=f"Failed to reset metrics: {str(e)}")


@router.post("/analysis/bee-preferences/", response_model=AnalysisJobResponse)
@monitor_performance("api_bee_preference_analysis")
@track_errors("api_analysis")
async def start_bee_preference_analysis(
    request: BeePreferenceRequest,
    db: Session = Depends(get_db)
):
    """Start bee preference analysis with comprehensive logging."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Bee preference analysis request received",
        request_id=req_id,
        correlation_id=corr_id,
        dataset_id=request.dataset_id,
        target_column=request.target_column,
        model_type=request.model_type,
        operation="api_bee_preference_analysis"
    )
    
    try:
        db_service = DatabaseService(db)
        
        # Verify dataset exists
        dataset = db_service.get_dataset(request.dataset_id)
        if not dataset:
            logger.warning(
                "Dataset not found for bee preference analysis",
                request_id=req_id,
                correlation_id=corr_id,
                dataset_id=request.dataset_id,
                operation="api_bee_preference_analysis"
            )
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Create analysis job
        job_create = AnalysisJobCreate(
            dataset_id=request.dataset_id,
            job_type="bee_preferences",
            parameters={
                "target_column": request.target_column,
                "model_type": request.model_type,
                "test_size": request.test_size
            }
        )
        analysis_job = db_service.create_analysis_job(job_create)
        
        # Start Celery task
        task = analyze_bee_preferences.delay(
            request.dataset_id,
            {
                "target_column": request.target_column,
                "model_type": request.model_type,
                "test_size": request.test_size
            }
        )
        
        # Update job with task ID
        db_service.update_job_status(
            analysis_job.id, 
            'running', 
            {'celery_task_id': task.id}
        )
        
        logger.info(
            "Bee preference analysis started successfully",
            request_id=req_id,
            correlation_id=corr_id,
            job_id=analysis_job.id,
            task_id=task.id,
            dataset_id=request.dataset_id,
            operation="api_bee_preference_analysis"
        )
        
        return analysis_job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Bee preference analysis failed to start",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=request.dataset_id,
            error=str(e),
            operation="api_bee_preference_analysis"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analysis/plant-recommendations/", response_model=AnalysisJobResponse)
@monitor_performance("api_plant_recommendations")
@track_errors("api_analysis")
async def start_plant_recommendation_analysis(
    request: PlantRecommendationRequest,
    db: Session = Depends(get_db)
):
    """Start plant recommendation analysis."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Plant recommendation analysis request received",
        request_id=req_id,
        correlation_id=corr_id,
        dataset_id=request.dataset_id,
        top_n=request.top_n,
        criteria=request.criteria,
        operation="api_plant_recommendations"
    )
    
    try:
        db_service = DatabaseService(db)
        
        # Verify dataset exists
        dataset = db_service.get_dataset(request.dataset_id)
        if not dataset:
            logger.warning(
                "Dataset not found for plant recommendation analysis",
                request_id=req_id,
                correlation_id=corr_id,
                dataset_id=request.dataset_id,
                operation="api_plant_recommendations"
            )
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Create analysis job
        job_create = AnalysisJobCreate(
            dataset_id=request.dataset_id,
            job_type="plant_recommendations",
            parameters={
                "top_n": request.top_n,
                "criteria": request.criteria
            }
        )
        analysis_job = db_service.create_analysis_job(job_create)
        
        # Start Celery task
        task = generate_plant_recommendations.delay(
            request.dataset_id,
            request.top_n
        )
        
        # Update job with task ID
        db_service.update_job_status(
            analysis_job.id, 
            'running', 
            {'celery_task_id': task.id}
        )
        
        logger.info(
            "Plant recommendation analysis started successfully",
            request_id=req_id,
            correlation_id=corr_id,
            job_id=analysis_job.id,
            task_id=task.id,
            dataset_id=request.dataset_id,
            operation="api_plant_recommendations"
        )
        
        return analysis_job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Plant recommendation analysis failed to start",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=request.dataset_id,
            error=str(e),
            operation="api_plant_recommendations"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analysis/seasonal/", response_model=AnalysisJobResponse)
@monitor_performance("api_seasonal_analysis")
@track_errors("api_analysis")
async def start_seasonal_analysis(
    dataset_id: int = Query(..., description="Dataset ID"),
    parameters: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """Start seasonal analysis."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Seasonal analysis request received",
        request_id=req_id,
        correlation_id=corr_id,
        dataset_id=dataset_id,
        parameters=parameters,
        operation="api_seasonal_analysis"
    )
    
    try:
        db_service = DatabaseService(db)
        
        # Verify dataset exists
        dataset = db_service.get_dataset(dataset_id)
        if not dataset:
            logger.warning(
                "Dataset not found for seasonal analysis",
                request_id=req_id,
                correlation_id=corr_id,
                dataset_id=dataset_id,
                operation="api_seasonal_analysis"
            )
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Create analysis job
        job_create = AnalysisJobCreate(
            dataset_id=dataset_id,
            job_type="seasonal_analysis",
            parameters=parameters or {}
        )
        analysis_job = db_service.create_analysis_job(job_create)
        
        # Start Celery task
        task = seasonal_analysis.delay(dataset_id, parameters or {})
        
        # Update job with task ID
        db_service.update_job_status(
            analysis_job.id, 
            'running', 
            {'celery_task_id': task.id}
        )
        
        logger.info(
            "Seasonal analysis started successfully",
            request_id=req_id,
            correlation_id=corr_id,
            job_id=analysis_job.id,
            task_id=task.id,
            dataset_id=dataset_id,
            operation="api_seasonal_analysis"
        )
        
        return analysis_job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Seasonal analysis failed to start",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            error=str(e),
            operation="api_seasonal_analysis"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analysis/site-comparison/", response_model=AnalysisJobResponse)
@monitor_performance("api_site_comparison")
@track_errors("api_analysis")
async def start_site_comparison_analysis(
    dataset_id: int = Query(..., description="Dataset ID"),
    parameters: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """Start site comparison analysis."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Site comparison analysis request received",
        request_id=req_id,
        correlation_id=corr_id,
        dataset_id=dataset_id,
        parameters=parameters,
        operation="api_site_comparison"
    )
    
    try:
        db_service = DatabaseService(db)
        
        # Verify dataset exists
        dataset = db_service.get_dataset(dataset_id)
        if not dataset:
            logger.warning(
                "Dataset not found for site comparison analysis",
                request_id=req_id,
                correlation_id=corr_id,
                dataset_id=dataset_id,
                operation="api_site_comparison"
            )
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Create analysis job
        job_create = AnalysisJobCreate(
            dataset_id=dataset_id,
            job_type="site_comparison",
            parameters=parameters or {}
        )
        analysis_job = db_service.create_analysis_job(job_create)
        
        # Start Celery task
        task = site_comparison.delay(dataset_id, parameters or {})
        
        # Update job with task ID
        db_service.update_job_status(
            analysis_job.id, 
            'running', 
            {'celery_task_id': task.id}
        )
        
        logger.info(
            "Site comparison analysis started successfully",
            request_id=req_id,
            correlation_id=corr_id,
            job_id=analysis_job.id,
            task_id=task.id,
            dataset_id=dataset_id,
            operation="api_site_comparison"
        )
        
        return analysis_job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Site comparison analysis failed to start",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            error=str(e),
            operation="api_site_comparison"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analysis/jobs/{job_id}", response_model=AnalysisJobResponse)
@monitor_performance("api_analysis_job_get")
@track_errors("api_analysis")
async def get_analysis_job(
    job_id: int = Path(..., description="Analysis job ID"),
    db: Session = Depends(get_db)
):
    """Get analysis job by ID."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Analysis job get request received",
        request_id=req_id,
        correlation_id=corr_id,
        job_id=job_id,
        operation="api_analysis_job_get"
    )
    
    try:
        db_service = DatabaseService(db)
        job = db_service.get_analysis_job(job_id)
        
        if not job:
            logger.warning(
                "Analysis job not found",
                request_id=req_id,
                correlation_id=corr_id,
                job_id=job_id,
                operation="api_analysis_job_get"
            )
            raise HTTPException(status_code=404, detail="Analysis job not found")
        
        logger.info(
            "Analysis job retrieved successfully",
            request_id=req_id,
            correlation_id=corr_id,
            job_id=job_id,
            job_type=job.job_type,
            status=job.status,
            operation="api_analysis_job_get"
        )
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Analysis job retrieval failed",
            request_id=req_id,
            correlation_id=corr_id,
            job_id=job_id,
            error=str(e),
            operation="api_analysis_job_get"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analysis/jobs/", response_model=List[AnalysisJobResponse])
@monitor_performance("api_analysis_job_list")
@track_errors("api_analysis")
async def list_analysis_jobs(
    dataset_id: Optional[int] = Query(None, description="Filter by dataset ID"),
    status: Optional[str] = Query(None, description="Filter by job status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_db)
):
    """List analysis jobs with filtering and pagination."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Analysis job list request received",
        request_id=req_id,
        correlation_id=corr_id,
        dataset_id=dataset_id,
        status=status,
        skip=skip,
        limit=limit,
        operation="api_analysis_job_list"
    )
    
    try:
        db_service = DatabaseService(db)
        jobs = db_service.list_analysis_jobs(
            dataset_id=dataset_id,
            status=status,
            skip=skip,
            limit=limit
        )
        
        logger.info(
            "Analysis jobs retrieved successfully",
            request_id=req_id,
            correlation_id=corr_id,
            jobs_count=len(jobs),
            dataset_id=dataset_id,
            status=status,
            operation="api_analysis_job_list"
        )
        
        return jobs
        
    except Exception as e:
        logger.error(
            "Analysis job list retrieval failed",
            request_id=req_id,
            correlation_id=corr_id,
            error=str(e),
            operation="api_analysis_job_list"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analysis/jobs/{job_id}/results")
@monitor_performance("api_analysis_results")
@track_errors("api_analysis")
async def get_analysis_results(
    job_id: int = Path(..., description="Analysis job ID"),
    db: Session = Depends(get_db)
):
    """Get analysis results."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Analysis results request received",
        request_id=req_id,
        correlation_id=corr_id,
        job_id=job_id,
        operation="api_analysis_results"
    )
    
    try:
        db_service = DatabaseService(db)
        job = db_service.get_analysis_job(job_id)
        
        if not job:
            logger.warning(
                "Analysis job not found for results",
                request_id=req_id,
                correlation_id=corr_id,
                job_id=job_id,
                operation="api_analysis_results"
            )
            raise HTTPException(status_code=404, detail="Analysis job not found")
        
        if job.status != 'completed':
            logger.warning(
                "Analysis job not completed",
                request_id=req_id,
                correlation_id=corr_id,
                job_id=job_id,
                status=job.status,
                operation="api_analysis_results"
            )
            raise HTTPException(
                status_code=400, 
                detail=f"Analysis job not completed. Current status: {job.status}"
            )
        
        response = {
            "job_id": job.id,
            "job_type": job.job_type,
            "status": job.status,
            "results": job.results,
            "completed_at": job.completed_at,
            "parameters": job.parameters
        }
        
        logger.info(
            "Analysis results retrieved successfully",
            request_id=req_id,
            correlation_id=corr_id,
            job_id=job_id,
            job_type=job.job_type,
            operation="api_analysis_results"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Analysis results retrieval failed",
            request_id=req_id,
            correlation_id=corr_id,
            job_id=job_id,
            error=str(e),
            operation="api_analysis_results"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analysis/jobs/{job_id}/status")
@monitor_performance("api_analysis_status")
@track_errors("api_analysis")
async def get_analysis_job_status(
    job_id: int = Path(..., description="Analysis job ID"),
    db: Session = Depends(get_db)
):
    """Get detailed analysis job status including Celery task status."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Analysis job status request received",
        request_id=req_id,
        correlation_id=corr_id,
        job_id=job_id,
        operation="api_analysis_status"
    )
    
    try:
        db_service = DatabaseService(db)
        job = db_service.get_analysis_job(job_id)
        
        if not job:
            logger.warning(
                "Analysis job not found for status",
                request_id=req_id,
                correlation_id=corr_id,
                job_id=job_id,
                operation="api_analysis_status"
            )
            raise HTTPException(status_code=404, detail="Analysis job not found")
        
        # Get Celery task status if available
        celery_status = None
        if job.celery_task_id:
            try:
                celery_status = get_task_status(job.celery_task_id)
            except Exception as e:
                logger.warning(
                    "Failed to get Celery task status",
                    request_id=req_id,
                    correlation_id=corr_id,
                    job_id=job_id,
                    celery_task_id=job.celery_task_id,
                    error=str(e),
                    operation="api_analysis_status"
                )
        
        response = {
            "job_id": job.id,
            "job_type": job.job_type,
            "status": job.status,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "celery_task_id": job.celery_task_id,
            "celery_status": celery_status,
            "parameters": job.parameters
        }
        
        logger.info(
            "Analysis job status retrieved successfully",
            request_id=req_id,
            correlation_id=corr_id,
            job_id=job_id,
            status=job.status,
            celery_status=celery_status.get('status') if celery_status else None,
            operation="api_analysis_status"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Analysis job status retrieval failed",
            request_id=req_id,
            correlation_id=corr_id,
            job_id=job_id,
            error=str(e),
            operation="api_analysis_status"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/analysis/jobs/{job_id}")
@monitor_performance("api_analysis_cancel")
@track_errors("api_analysis")
async def cancel_analysis_job(
    job_id: int = Path(..., description="Analysis job ID"),
    db: Session = Depends(get_db)
):
    """Cancel a running analysis job."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Analysis job cancel request received",
        request_id=req_id,
        correlation_id=corr_id,
        job_id=job_id,
        operation="api_analysis_cancel"
    )
    
    try:
        db_service = DatabaseService(db)
        job = db_service.get_analysis_job(job_id)
        
        if not job:
            logger.warning(
                "Analysis job not found for cancellation",
                request_id=req_id,
                correlation_id=corr_id,
                job_id=job_id,
                operation="api_analysis_cancel"
            )
            raise HTTPException(status_code=404, detail="Analysis job not found")
        
        if job.status not in ['pending', 'running']:
            logger.warning(
                "Analysis job cannot be cancelled - not in cancellable state",
                request_id=req_id,
                correlation_id=corr_id,
                job_id=job_id,
                status=job.status,
                operation="api_analysis_cancel"
            )
            raise HTTPException(
                status_code=400, 
                detail=f"Job cannot be cancelled. Current status: {job.status}"
            )
        
        # Cancel Celery task if available
        celery_cancelled = False
        if job.celery_task_id:
            try:
                celery_cancelled = cancel_task(job.celery_task_id)
            except Exception as e:
                logger.warning(
                    "Failed to cancel Celery task",
                    request_id=req_id,
                    correlation_id=corr_id,
                    job_id=job_id,
                    celery_task_id=job.celery_task_id,
                    error=str(e),
                    operation="api_analysis_cancel"
                )
        
        # Update job status
        db_service.update_job_status(job_id, 'cancelled')
        
        logger.info(
            "Analysis job cancelled successfully",
            request_id=req_id,
            correlation_id=corr_id,
            job_id=job_id,
            celery_cancelled=celery_cancelled,
            operation="api_analysis_cancel"
        )
        
        return SuccessResponse(message="Analysis job cancelled successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Analysis job cancellation failed",
            request_id=req_id,
            correlation_id=corr_id,
            job_id=job_id,
            error=str(e),
            operation="api_analysis_cancel"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analysis/stats")
@monitor_performance("api_analysis_stats")
@track_errors("api_analysis")
async def get_analysis_statistics(
    db: Session = Depends(get_db)
):
    """Get analysis statistics and summary."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Analysis statistics request received",
        request_id=req_id,
        correlation_id=corr_id,
        operation="api_analysis_stats"
    )
    
    try:
        db_service = DatabaseService(db)
        stats = db_service.get_database_stats()
        
        logger.info(
            "Analysis statistics retrieved successfully",
            request_id=req_id,
            correlation_id=corr_id,
            total_jobs=stats.get('total_jobs', 0),
            operation="api_analysis_stats"
        )
        
        return stats
        
    except Exception as e:
        logger.error(
            "Analysis statistics retrieval failed",
            request_id=req_id,
            correlation_id=corr_id,
            error=str(e),
            operation="api_analysis_stats"
        )
        raise HTTPException(status_code=500, detail="Internal server error") 