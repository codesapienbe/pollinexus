"""
Main FastAPI application for Pollinexus API.

This module configures the FastAPI application with all routes,
middleware, and error handling.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uuid
from typing import Dict, Any

from ..core.config import settings
from ..core.logging import logger, request_id, correlation_id
from ..core.metrics import monitor_performance
from ..core.error_tracking import track_errors, error_tracker
from .routes import datasets, analysis, visualizations


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    
    # Startup
    logger.info(
        "Pollinexus API starting up",
        version=settings.version,
        environment=settings.environment,
        log_level=settings.log_level,
        operation="app_startup"
    )
    
    # Initialize error tracker
    error_tracker.initialize()
    
    yield
    
    # Shutdown
    logger.info(
        "Pollinexus API shutting down",
        operation="app_shutdown"
    )


# Create FastAPI application
app = FastAPI(
    title="Pollinexus API",
    description="Data-Driven Pollinator Conservation API for Environmental Agencies",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "https://pollinex.us",
        "https://www.pollinex.us"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add TrustedHost middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "host.docker.internal",
        "pollinex.us",
        "www.pollinex.us"
    ]
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Middleware for comprehensive request logging and correlation ID management."""
    
    # Generate correlation ID for request tracking
    corr_id = str(uuid.uuid4())
    correlation_id.set(corr_id)
    
    # Generate request ID
    req_id = str(uuid.uuid4())
    request_id.set(req_id)
    
    # Log request start
    start_time = time.time()
    
    logger.info(
        "API request started",
        request_id=req_id,
        correlation_id=corr_id,
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        operation="api_request_start"
    )
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log request completion
        logger.info(
            "API request completed",
            request_id=req_id,
            correlation_id=corr_id,
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
            operation="api_request_complete"
        )
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = corr_id
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log request error
        logger.error(
            "API request failed",
            request_id=req_id,
            correlation_id=corr_id,
            method=request.method,
            url=str(request.url),
            error=str(e),
            process_time=process_time,
            operation="api_request_error"
        )
        
        # Track error
        error_tracker.track_error(
            error_type="api_request_error",
            error_message=str(e),
            context={
                "request_id": req_id,
                "correlation_id": corr_id,
                "method": request.method,
                "url": str(request.url),
                "process_time": process_time
            }
        )
        
        # Re-raise the exception
        raise


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler with comprehensive logging."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.warning(
        "HTTP exception occurred",
        request_id=req_id,
        correlation_id=corr_id,
        method=request.method,
        url=str(request.url),
        status_code=exc.status_code,
        detail=exc.detail,
        operation="http_exception"
    )
    
    # Track error
    error_tracker.track_error(
        error_type="http_exception",
        error_message=exc.detail,
        context={
            "request_id": req_id,
            "correlation_id": corr_id,
            "status_code": exc.status_code,
            "method": request.method,
            "url": str(request.url)
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": req_id,
            "correlation_id": corr_id
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unexpected errors."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.error(
        "Unexpected error occurred",
        request_id=req_id,
        correlation_id=corr_id,
        method=request.method,
        url=str(request.url),
        error=str(exc),
        error_type=type(exc).__name__,
        operation="unexpected_error"
    )
    
    # Track error
    error_tracker.track_error(
        error_type="unexpected_error",
        error_message=str(exc),
        context={
            "request_id": req_id,
            "correlation_id": corr_id,
            "error_type": type(exc).__name__,
            "method": request.method,
            "url": str(request.url)
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred",
            "request_id": req_id,
            "correlation_id": corr_id
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
@monitor_performance("health_check")
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Health check requested",
        request_id=req_id,
        correlation_id=corr_id,
        operation="health_check"
    )
    
    try:
        # Basic health check
        health_status = {
            "status": "healthy",
            "version": settings.version,
            "environment": settings.environment,
            "timestamp": time.time(),
            "request_id": req_id,
            "correlation_id": corr_id
        }
        
        logger.info(
            "Health check completed successfully",
            request_id=req_id,
            correlation_id=corr_id,
            operation="health_check"
        )
        
        return health_status
        
    except Exception as e:
        logger.error(
            "Health check failed",
            request_id=req_id,
            correlation_id=corr_id,
            error=str(e),
            operation="health_check"
        )
        
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "request_id": req_id,
                "correlation_id": corr_id
            }
        )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Root endpoint accessed",
        request_id=req_id,
        correlation_id=corr_id,
        operation="root_access"
    )
    
    return {
        "message": "Welcome to Pollinexus API",
        "description": "Data-Driven Pollinator Conservation API for Environmental Agencies",
        "version": settings.version,
        "environment": settings.environment,
        "documentation": "/docs",
        "health_check": "/health",
        "request_id": req_id,
        "correlation_id": corr_id
    }


# Include API routes with proper prefixing and tags
app.include_router(
    datasets.router,
    prefix="/api/v1",
    tags=["Datasets"],
    responses={404: {"description": "Not found"}}
)

app.include_router(
    analysis.router,
    prefix="/api/v1",
    tags=["Analysis"],
    responses={404: {"description": "Not found"}}
)

app.include_router(
    visualizations.router,
    prefix="/api/v1",
    tags=["Visualizations"],
    responses={404: {"description": "Not found"}}
)


# API information endpoint
@app.get("/api/v1/info", tags=["API Info"])
async def api_info():
    """Get comprehensive API information and capabilities."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "API info requested",
        request_id=req_id,
        correlation_id=corr_id,
        operation="api_info"
    )
    
    api_info = {
        "name": "Pollinexus API",
        "version": settings.version,
        "description": "Data-Driven Pollinator Conservation API for Environmental Agencies",
        "environment": settings.environment,
        "base_url": "/api/v1",
        "endpoints": {
            "datasets": {
                "count": 8,
                "base_path": "/api/v1/datasets",
                "operations": ["create", "read", "update", "delete", "search", "health"]
            },
            "analysis": {
                "count": 10,
                "base_path": "/api/v1/analysis",
                "operations": ["bee_preferences", "plant_recommendations", "seasonal", "site_comparison", "jobs"]
            },
            "visualizations": {
                "count": 9,
                "base_path": "/api/v1/visualizations",
                "operations": ["bee_distribution", "seasonal_patterns", "site_comparison", "dashboard", "batch"]
            }
        },
        "features": {
            "file_upload": True,
            "background_processing": True,
            "real_time_monitoring": True,
            "batch_operations": True,
            "search_and_filtering": True,
            "health_monitoring": True
        },
        "documentation": {
            "interactive_docs": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        "request_id": req_id,
        "correlation_id": corr_id
    }
    
    logger.info(
        "API info retrieved successfully",
        request_id=req_id,
        correlation_id=corr_id,
        operation="api_info"
    )
    
    return api_info


# Metrics endpoint for monitoring
@app.get("/api/v1/metrics", tags=["Monitoring"])
@monitor_performance("metrics_endpoint")
async def get_metrics():
    """Get API metrics and performance statistics."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Metrics requested",
        request_id=req_id,
        correlation_id=corr_id,
        operation="metrics_endpoint"
    )
    
    try:
        # Get basic metrics
        metrics = {
            "timestamp": time.time(),
            "version": settings.version,
            "environment": settings.environment,
            "uptime": time.time(),  # Would be calculated from startup time
            "request_id": req_id,
            "correlation_id": corr_id
        }
        
        logger.info(
            "Metrics retrieved successfully",
            request_id=req_id,
            correlation_id=corr_id,
            operation="metrics_endpoint"
        )
        
        return metrics
        
    except Exception as e:
        logger.error(
            "Metrics retrieval failed",
            request_id=req_id,
            correlation_id=corr_id,
            error=str(e),
            operation="metrics_endpoint"
        )
        
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "pollinexus.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    ) 