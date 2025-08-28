"""
Visualization routes for Pollinexus API.

This module contains all endpoints related to data visualization operations
with comprehensive logging and monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import time
from pathlib import Path as PathLib

from ...core.database import get_db
from ...services.database_service import DatabaseService
from ...tasks.celery_app import celery_app, get_task_status, cancel_task
from ...tasks.visualization import (
    create_bee_distribution_plot,
    create_seasonal_patterns_plot,
    create_site_comparison_plot,
    create_interactive_dashboard
)
from ...core.logging import logger, request_id, correlation_id
from ...core.metrics import monitor_performance
from ...core.error_tracking import track_errors, error_tracker
from ..models.requests import VisualizationRequest
from ..models.responses import (
    VisualizationResponse,
    SuccessResponse,
    ErrorResponse
)

router = APIRouter(tags=["3 - Visualizations"])


@router.post("/visualizations/bee-distribution/", response_model=VisualizationResponse, tags=["📈 Data Visualizations"])
@monitor_performance("api_bee_distribution_visualization")
@track_errors("api_visualization")
async def create_bee_distribution_visualization(
    dataset_id: int = Query(..., description="Dataset ID"),
    parameters: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """Create bee species distribution visualization."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Bee distribution visualization request received",
        request_id=req_id,
        correlation_id=corr_id,
        dataset_id=dataset_id,
        parameters=parameters,
        operation="api_bee_distribution_visualization"
    )
    
    try:
        db_service = DatabaseService(db)
        
        # Verify dataset exists
        dataset = db_service.get_dataset(dataset_id)
        if not dataset:
            logger.warning(
                "Dataset not found for bee distribution visualization",
                request_id=req_id,
                correlation_id=corr_id,
                dataset_id=dataset_id,
                operation="api_bee_distribution_visualization"
            )
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Start Celery task
        task = create_bee_distribution_plot.delay(dataset_id, parameters or {})
        
        # Create visualization record
        visualization = {
            "id": int(time.time()),  # Simple ID generation
            "dataset_id": dataset_id,
            "plot_type": "bee_distribution",
            "plot_data": {"task_id": task.id},
            "plot_config": parameters or {},
            "created_at": time.time()
        }
        
        logger.info(
            "Bee distribution visualization started successfully",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            task_id=task.id,
            operation="api_bee_distribution_visualization"
        )
        
        return visualization
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Bee distribution visualization failed to start",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            error=str(e),
            operation="api_bee_distribution_visualization"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/visualizations/seasonal-patterns/", response_model=VisualizationResponse, tags=["📈 Data Visualizations"])
@monitor_performance("api_seasonal_patterns_visualization")
@track_errors("api_visualization")
async def create_seasonal_patterns_visualization(
    dataset_id: int = Query(..., description="Dataset ID"),
    parameters: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """Create seasonal patterns visualization."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Seasonal patterns visualization request received",
        request_id=req_id,
        correlation_id=corr_id,
        dataset_id=dataset_id,
        parameters=parameters,
        operation="api_seasonal_patterns_visualization"
    )
    
    try:
        db_service = DatabaseService(db)
        
        # Verify dataset exists
        dataset = db_service.get_dataset(dataset_id)
        if not dataset:
            logger.warning(
                "Dataset not found for seasonal patterns visualization",
                request_id=req_id,
                correlation_id=corr_id,
                dataset_id=dataset_id,
                operation="api_seasonal_patterns_visualization"
            )
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Start Celery task
        task = create_seasonal_patterns_plot.delay(dataset_id, parameters or {})
        
        # Create visualization record
        visualization = {
            "id": int(time.time()),
            "dataset_id": dataset_id,
            "plot_type": "seasonal_patterns",
            "plot_data": {"task_id": task.id},
            "plot_config": parameters or {},
            "created_at": time.time()
        }
        
        logger.info(
            "Seasonal patterns visualization started successfully",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            task_id=task.id,
            operation="api_seasonal_patterns_visualization"
        )
        
        return visualization
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Seasonal patterns visualization failed to start",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            error=str(e),
            operation="api_seasonal_patterns_visualization"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/visualizations/site-comparison/", response_model=VisualizationResponse, tags=["📈 Data Visualizations"])
@monitor_performance("api_site_comparison_visualization")
@track_errors("api_visualization")
async def create_site_comparison_visualization(
    dataset_id: int = Query(..., description="Dataset ID"),
    parameters: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """Create site comparison visualization."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Site comparison visualization request received",
        request_id=req_id,
        correlation_id=corr_id,
        dataset_id=dataset_id,
        parameters=parameters,
        operation="api_site_comparison_visualization"
    )
    
    try:
        db_service = DatabaseService(db)
        
        # Verify dataset exists
        dataset = db_service.get_dataset(dataset_id)
        if not dataset:
            logger.warning(
                "Dataset not found for site comparison visualization",
                request_id=req_id,
                correlation_id=corr_id,
                dataset_id=dataset_id,
                operation="api_site_comparison_visualization"
            )
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Start Celery task
        task = create_site_comparison_plot.delay(dataset_id, parameters or {})
        
        # Create visualization record
        visualization = {
            "id": int(time.time()),
            "dataset_id": dataset_id,
            "plot_type": "site_comparison",
            "plot_data": {"task_id": task.id},
            "plot_config": parameters or {},
            "created_at": time.time()
        }
        
        logger.info(
            "Site comparison visualization started successfully",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            task_id=task.id,
            operation="api_site_comparison_visualization"
        )
        
        return visualization
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Site comparison visualization failed to start",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            error=str(e),
            operation="api_site_comparison_visualization"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/visualizations/dashboard/", response_model=VisualizationResponse, tags=["📈 Data Visualizations"])
@monitor_performance("api_interactive_dashboard")
@track_errors("api_visualization")
async def create_interactive_dashboard_visualization(
    dataset_id: int = Query(..., description="Dataset ID"),
    parameters: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """Create comprehensive interactive dashboard."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Interactive dashboard visualization request received",
        request_id=req_id,
        correlation_id=corr_id,
        dataset_id=dataset_id,
        parameters=parameters,
        operation="api_interactive_dashboard"
    )
    
    try:
        db_service = DatabaseService(db)
        
        # Verify dataset exists
        dataset = db_service.get_dataset(dataset_id)
        if not dataset:
            logger.warning(
                "Dataset not found for interactive dashboard visualization",
                request_id=req_id,
                correlation_id=corr_id,
                dataset_id=dataset_id,
                operation="api_interactive_dashboard"
            )
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Start Celery task
        task = create_interactive_dashboard.delay(dataset_id, parameters or {})
        
        # Create visualization record
        visualization = {
            "id": int(time.time()),
            "dataset_id": dataset_id,
            "plot_type": "interactive_dashboard",
            "plot_data": {"task_id": task.id},
            "plot_config": parameters or {},
            "created_at": time.time()
        }
        
        logger.info(
            "Interactive dashboard visualization started successfully",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            task_id=task.id,
            operation="api_interactive_dashboard"
        )
        
        return visualization
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Interactive dashboard visualization failed to start",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=dataset_id,
            error=str(e),
            operation="api_interactive_dashboard"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/visualizations/batch/", response_model=List[VisualizationResponse], tags=["📈 Data Visualizations"])
@monitor_performance("api_batch_visualization")
@track_errors("api_visualization")
async def create_batch_visualizations(
    request: VisualizationRequest,
    db: Session = Depends(get_db)
):
    """Create multiple visualizations in batch."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Batch visualization request received",
        request_id=req_id,
        correlation_id=corr_id,
        dataset_id=request.dataset_id,
        plot_types=request.plot_types,
        operation="api_batch_visualization"
    )
    
    try:
        db_service = DatabaseService(db)
        
        # Verify dataset exists
        dataset = db_service.get_dataset(request.dataset_id)
        if not dataset:
            logger.warning(
                "Dataset not found for batch visualization",
                request_id=req_id,
                correlation_id=corr_id,
                dataset_id=request.dataset_id,
                operation="api_batch_visualization"
            )
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Map plot types to tasks
        task_mapping = {
            "bee_distribution": create_bee_distribution_plot,
            "seasonal_patterns": create_seasonal_patterns_plot,
            "site_comparison": create_site_comparison_plot,
            "interactive_dashboard": create_interactive_dashboard
        }
        
        visualizations = []
        tasks = []
        
        # Start tasks for each plot type
        for plot_type in request.plot_types:
            if plot_type in task_mapping:
                task = task_mapping[plot_type].delay(
                    request.dataset_id, 
                    request.parameters or {}
                )
                tasks.append(task)
                
                visualization = {
                    "id": int(time.time()) + len(visualizations),
                    "dataset_id": request.dataset_id,
                    "plot_type": plot_type,
                    "plot_data": {"task_id": task.id},
                    "plot_config": request.parameters or {},
                    "created_at": time.time()
                }
                visualizations.append(visualization)
            else:
                logger.warning(
                    "Unknown plot type requested",
                    request_id=req_id,
                    correlation_id=corr_id,
                    plot_type=plot_type,
                    operation="api_batch_visualization"
                )
        
        logger.info(
            "Batch visualization started successfully",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=request.dataset_id,
            plot_types=request.plot_types,
            tasks_started=len(tasks),
            operation="api_batch_visualization"
        )
        
        return visualizations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Batch visualization failed to start",
            request_id=req_id,
            correlation_id=corr_id,
            dataset_id=request.dataset_id,
            error=str(e),
            operation="api_batch_visualization"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/visualizations/{visualization_id}/status", tags=["📈 Data Visualizations"])
@monitor_performance("api_visualization_status")
@track_errors("api_visualization")
async def get_visualization_status(
    visualization_id: int = Path(..., description="Visualization ID"),
    task_id: str = Query(..., description="Celery task ID")
):
    """Get visualization task status."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Visualization status request received",
        request_id=req_id,
        correlation_id=corr_id,
        visualization_id=visualization_id,
        task_id=task_id,
        operation="api_visualization_status"
    )
    
    try:
        # Get Celery task status
        task_status = get_task_status(task_id)
        
        response = {
            "visualization_id": visualization_id,
            "task_id": task_id,
            "status": task_status.get('status'),
            "ready": task_status.get('ready', False),
            "successful": task_status.get('successful', False),
            "failed": task_status.get('failed', False),
            "info": task_status.get('info'),
            "traceback": task_status.get('traceback')
        }
        
        logger.info(
            "Visualization status retrieved successfully",
            request_id=req_id,
            correlation_id=corr_id,
            visualization_id=visualization_id,
            task_id=task_id,
            status=task_status.get('status'),
            operation="api_visualization_status"
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Visualization status retrieval failed",
            request_id=req_id,
            correlation_id=corr_id,
            visualization_id=visualization_id,
            task_id=task_id,
            error=str(e),
            operation="api_visualization_status"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/visualizations/{visualization_id}/download", tags=["📈 Data Visualizations"])
@monitor_performance("api_visualization_download")
@track_errors("api_visualization")
async def download_visualization(
    visualization_id: int = Path(..., description="Visualization ID"),
    task_id: str = Query(..., description="Celery task ID")
):
    """Download visualization file."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Visualization download request received",
        request_id=req_id,
        correlation_id=corr_id,
        visualization_id=visualization_id,
        task_id=task_id,
        operation="api_visualization_download"
    )
    
    try:
        # Get task result
        task_result = celery_app.AsyncResult(task_id)
        
        if not task_result.ready():
            logger.warning(
                "Visualization not ready for download",
                request_id=req_id,
                correlation_id=corr_id,
                visualization_id=visualization_id,
                task_id=task_id,
                status=task_result.status,
                operation="api_visualization_download"
            )
            raise HTTPException(
                status_code=400, 
                detail="Visualization not ready for download"
            )
        
        if task_result.failed():
            logger.error(
                "Visualization task failed",
                request_id=req_id,
                correlation_id=corr_id,
                visualization_id=visualization_id,
                task_id=task_id,
                error=task_result.traceback,
                operation="api_visualization_download"
            )
            raise HTTPException(
                status_code=500, 
                detail="Visualization generation failed"
            )
        
        # Get result
        result = task_result.get()
        plot_path = result.get('plot_path')
        
        if not plot_path or not PathLib(plot_path).exists():
            logger.error(
                "Visualization file not found",
                request_id=req_id,
                correlation_id=corr_id,
                visualization_id=visualization_id,
                task_id=task_id,
                plot_path=plot_path,
                operation="api_visualization_download"
            )
            raise HTTPException(
                status_code=404, 
                detail="Visualization file not found"
            )
        
        # Return file info
        file_info = {
            "visualization_id": visualization_id,
            "task_id": task_id,
            "plot_path": plot_path,
            "plot_filename": result.get('plot_filename'),
            "plot_type": result.get('plot_type'),
            "file_size": PathLib(plot_path).stat().st_size,
            "download_url": f"/api/v1/visualizations/{visualization_id}/file"
        }
        
        logger.info(
            "Visualization download info retrieved successfully",
            request_id=req_id,
            correlation_id=corr_id,
            visualization_id=visualization_id,
            task_id=task_id,
            plot_path=plot_path,
            operation="api_visualization_download"
        )
        
        return file_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Visualization download failed",
            request_id=req_id,
            correlation_id=corr_id,
            visualization_id=visualization_id,
            task_id=task_id,
            error=str(e),
            operation="api_visualization_download"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/visualizations/{visualization_id}", tags=["📈 Data Visualizations"])
@monitor_performance("api_visualization_cancel")
@track_errors("api_visualization")
async def cancel_visualization(
    visualization_id: int = Path(..., description="Visualization ID"),
    task_id: str = Query(..., description="Celery task ID")
):
    """Cancel a running visualization task."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Visualization cancel request received",
        request_id=req_id,
        correlation_id=corr_id,
        visualization_id=visualization_id,
        task_id=task_id,
        operation="api_visualization_cancel"
    )
    
    try:
        # Cancel Celery task
        success = cancel_task(task_id)
        
        if success:
            logger.info(
                "Visualization cancelled successfully",
                request_id=req_id,
                correlation_id=corr_id,
                visualization_id=visualization_id,
                task_id=task_id,
                operation="api_visualization_cancel"
            )
            return SuccessResponse(message="Visualization cancelled successfully")
        else:
            logger.warning(
                "Visualization could not be cancelled",
                request_id=req_id,
                correlation_id=corr_id,
                visualization_id=visualization_id,
                task_id=task_id,
                operation="api_visualization_cancel"
            )
            raise HTTPException(
                status_code=400, 
                detail="Visualization could not be cancelled"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Visualization cancellation failed",
            request_id=req_id,
            correlation_id=corr_id,
            visualization_id=visualization_id,
            task_id=task_id,
            error=str(e),
            operation="api_visualization_cancel"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/visualizations/available-types", tags=["📈 Data Visualizations"])
@monitor_performance("api_visualization_types")
@track_errors("api_visualization")
async def get_available_visualization_types():
    """Get list of available visualization types."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Available visualization types request received",
        request_id=req_id,
        correlation_id=corr_id,
        operation="api_visualization_types"
    )
    
    try:
        visualization_types = [
            {
                "type": "bee_distribution",
                "name": "Bee Species Distribution",
                "description": "Interactive bar chart showing bee species distribution",
                "parameters": {
                    "top_n": "Number of top species to display (default: 20)"
                }
            },
            {
                "type": "seasonal_patterns",
                "name": "Seasonal Patterns",
                "description": "Multi-panel analysis of seasonal bee activity patterns",
                "parameters": {
                    "include_trends": "Include trend lines (default: true)"
                }
            },
            {
                "type": "site_comparison",
                "name": "Site Comparison",
                "description": "Comparison of bee activity across different sites",
                "parameters": {
                    "metrics": "Metrics to compare (default: ['total_bees', 'diversity'])"
                }
            },
            {
                "type": "interactive_dashboard",
                "name": "Interactive Dashboard",
                "description": "Comprehensive dashboard with multiple visualizations",
                "parameters": {
                    "include_timeline": "Include timeline view (default: true)",
                    "include_metrics": "Include summary metrics (default: true)"
                }
            }
        ]
        
        logger.info(
            "Available visualization types retrieved successfully",
            request_id=req_id,
            correlation_id=corr_id,
            types_count=len(visualization_types),
            operation="api_visualization_types"
        )
        
        return {
            "visualization_types": visualization_types,
            "total_types": len(visualization_types)
        }
        
    except Exception as e:
        logger.error(
            "Available visualization types retrieval failed",
            request_id=req_id,
            correlation_id=corr_id,
            error=str(e),
            operation="api_visualization_types"
        )
        raise HTTPException(status_code=500, detail="Internal server error") 