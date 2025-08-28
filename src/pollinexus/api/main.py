"""
Main FastAPI application for Pollinexus API.

This module configures the FastAPI application with all routes,
middleware, and error handling.
"""

from fastapi import FastAPI, Request, HTTPException, Depends, Body, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
import time
import uuid
import traceback
from typing import Dict, Any
import tempfile
import subprocess
import shutil
import os

from ..core.config import settings
from ..core.logging import logger, request_id, correlation_id
from ..core.metrics import monitor_performance
from ..core.error_tracking import track_errors, error_tracker
from ..core.auth import get_current_user, verify_otp_and_generate_token
from ..core.security import create_security_middleware, security_monitor
from ..core.health import health_monitor, get_health_status, get_quick_health
from ..core.shutdown import shutdown_manager, shutdown_context
from ..core.shutdown_monitoring import shutdown_monitor
from ..services.user_service import UserService
from .routes import datasets, analysis, visualizations
from .models.user_models import (
    UserRegistration, UserLoginRequest, VerifyOTPRequest, VerificationRequest,
    UserResponseWithId, TokenResponse, VerificationResponse, UserResponseWithFaces
)
from ..core.database import create_tables

try:
    import mermaid as mermaid_py  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    mermaid_py = None

try:
    import cairosvg  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    cairosvg = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    
    # Startup
    logger.info(
        "Pollinexus API starting up",
        extra={
            "version": settings.version,
            "environment": settings.environment,
            "log_level": settings.log_level,
            "operation": "app_startup"
        }
    )
    
    # Initialize error tracker
    error_tracker.initialize()

    # Reset OpenAPI schema to avoid any stale caching between reloads
    app.openapi_schema = None

    # Ensure database tables exist (idempotent)
    try:
        create_tables()
        logger.info(
            "Database tables created successfully",
            extra={
                "operation": "app_startup",
                "component": "database",
                "action": "create_tables"
            }
        )
    except Exception as e:
        logger.error(
            "Failed to create database tables - application cannot start",
            extra={
                "operation": "app_startup",
                "component": "database",
                "action": "create_tables",
                "error": str(e)
            }
        )
        # Fail fast - don't start the app without database tables
        raise RuntimeError(f"Database initialization failed: {e}")
    
    # Register application-specific cleanup handlers
    def cleanup_application_resources():
        """Clean up application-specific resources."""
        try:
            logger.info("Cleaning up application resources...")
            
            # Close any open file handles
            import gc
            gc.collect()
            
            logger.info("Application resources cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup application resources: {e}")
    
    shutdown_manager.register_cleanup_handler(cleanup_application_resources)
    
    yield
    
    # Shutdown - use graceful shutdown manager only outside development
    if not settings.is_development:
        async with shutdown_context():
            logger.info(
                "Pollinexus API shutting down",
                extra={"operation": "app_shutdown"}
            )


# Create FastAPI application
# Scenario-based OpenAPI tags for simple grouping
openapi_tags = [
    {"name": "🔧 Setup, Data Loading, and System Monitoring", "description": "Setup, data loading, health, security, metrics, shutdown."},
    {"name": "🔍 Data Quality Assessment", "description": "Validation, dataset health, profiling."},
    {"name": "🧹 Data Cleaning and Preprocessing", "description": "Dataset updates and cleanup operations."},
    {"name": "📊 Exploratory Data Analysis (EDA)", "description": "Searching, listing, site comparisons, stats."},
    {"name": "📈 Data Visualizations", "description": "Charts and dashboards."},
    {"name": "🤖 Machine Learning Analysis", "description": "Bee preferences and ML-driven analyses."},
    {"name": "🌱 Plant Species Analysis and Ranking", "description": "Plant recommendation analysis and ranking."},
    {"name": "🏆 Top 3 Plant Recommendations", "description": "Top-N recommendation outcomes and insights."},
    {"name": "📅 Seasonal Coverage Analysis", "description": "Seasonal trend and coverage analyses."},
    {"name": "🎯 Conclusions and Strategic Recommendations", "description": "Summary insights and strategic guidance."},
    {"name": "📄 Project Summary", "description": "High-level API and project summary info."}
]

app = FastAPI(
    title="Pollinexus API",
    description="Data-Driven Pollinator Conservation API for Environmental Agencies",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    openapi_tags=openapi_tags
)

# Add Security middleware only for non-local development
if not settings.disable_security_for_local and not settings.is_development:
    logger.info(
        "Adding security middleware for production environment",
        extra={
            "environment": settings.environment,
            "operation": "app_startup"
        }
    )
    app.add_middleware(create_security_middleware)
else:
    logger.info(
        "Security middleware disabled for local development",
        extra={
            "environment": settings.environment,
            "disable_security_for_local": settings.disable_security_for_local,
            "is_development": settings.is_development,
            "operation": "app_startup"
        }
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add TrustedHost middleware only for production
if not settings.disable_security_for_local and not settings.is_development:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts
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
        extra={
            "request_id": req_id,
            "correlation_id": corr_id,
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "operation": "api_request_start"
        }
    )
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log request completion
        logger.info(
            "API request completed",
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "process_time": process_time,
                "operation": "api_request_complete"
            }
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
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "method": request.method,
                "url": str(request.url),
                "error": str(e),
                "process_time": process_time,
                "operation": "api_request_error"
            }
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
        extra={
            "request_id": req_id,
            "correlation_id": corr_id,
            "method": request.method,
            "url": str(request.url),
            "status_code": exc.status_code,
            "detail": exc.detail,
            "operation": "http_exception"
        }
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
        extra={
            "request_id": req_id,
            "correlation_id": corr_id,
            "method": request.method,
            "url": str(request.url),
            "error": str(exc),
            "error_type": type(exc).__name__,
            "operation": "unexpected_error"
        }
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


# Enhanced Health check endpoints
@app.get("/api/v1/health", tags=["🔧 Setup, Data Loading, and System Monitoring"])
@monitor_performance("health_check")
async def health_check():
    """Quick health check endpoint for load balancers."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Health check requested",
        extra={
            "request_id": req_id,
            "correlation_id": corr_id,
            "operation": "health_check"
        }
    )
    
    try:
        health_status = await get_quick_health()
        health_status.update({
            "request_id": req_id,
            "correlation_id": corr_id,
            "version": settings.version,
            "environment": settings.environment
        })
        
        # Return appropriate HTTP status code
        status_code = 200 if health_status["status"] == "healthy" else 503
        
        logger.info(
            "Health check completed",
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "status": health_status["status"],
                "operation": "health_check"
            }
        )
        
        return JSONResponse(status_code=status_code, content=health_status)
        
    except Exception as e:
        logger.error(
            "Health check failed",
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "error": str(e),
                "operation": "health_check"
            }
        )
        
        return JSONResponse(
            status_code=503,
            content={
                "status": "critical",
                "error": str(e),
                "request_id": req_id,
                "correlation_id": corr_id,
                "version": settings.version,
                "environment": settings.environment
            }
        )


@app.get("/api/v1/health/detailed", tags=["🔧 Setup, Data Loading, and System Monitoring"])
@monitor_performance("health_check_detailed")
async def detailed_health_check():
    """Comprehensive health check with all system components."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    try:
        health_status = await get_health_status()
        
        # Ensure health_status is a dictionary
        if not isinstance(health_status, dict):
            logger.error("Health status is not a dictionary", extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "health_status_type": type(health_status).__name__,
                "operation": "health_check_detailed"
            })
            health_status = {
                "status": "critical",
                "message": "Health check system error",
                "error": "Invalid health status format"
            }
        
        # Add request metadata
        if req_id:
            health_status["request_id"] = req_id
        if corr_id:
            health_status["correlation_id"] = corr_id
        
        # Return appropriate HTTP status code
        status_code = 200 if health_status.get("status") == "healthy" else 503
        
        return JSONResponse(status_code=status_code, content=health_status)
        
    except Exception as e:
        logger.error(
            "Detailed health check failed",
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "operation": "health_check_detailed"
            }
        )
        
        return JSONResponse(
            status_code=503,
            content={
                "status": "critical",
                "error": str(e),
                "request_id": req_id,
                "correlation_id": corr_id
            }
        )


@app.get("/api/v1/security/status", tags=["🔧 Setup, Data Loading, and System Monitoring"])
@monitor_performance("security_status")
async def security_status():
    """Get security monitoring status and violation summary."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    try:
        violation_summary = security_monitor.get_violation_summary()
        
        return {
            "timestamp": time.time(),
            "request_id": req_id,
            "correlation_id": corr_id,
            "security_status": "active",
            "violations": violation_summary
        }
        
    except Exception as e:
        logger.error(
            "Security status check failed",
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "error": str(e),
                "operation": "security_status"
            }
        )
        
        raise HTTPException(status_code=500, detail="Failed to retrieve security status")


@app.get("/api/v1/shutdown/status", tags=["🔧 Setup, Data Loading, and System Monitoring"])
@monitor_performance("shutdown_status")
async def shutdown_status():
    """Get shutdown manager status and configuration."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    try:
        status = shutdown_manager.get_shutdown_status()
        
        return {
            "timestamp": time.time(),
            "request_id": req_id,
            "correlation_id": corr_id,
            "shutdown_status": status,
            "graceful_timeout": 30,
            "force_timeout": 5
        }
        
    except Exception as e:
        logger.error(
            "Shutdown status check failed",
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "error": str(e),
                "operation": "shutdown_status"
            }
        )
        
        raise HTTPException(status_code=500, detail="Failed to retrieve shutdown status")


@app.get("/api/v1/shutdown/metrics", tags=["🔧 Setup, Data Loading, and System Monitoring"])
@monitor_performance("shutdown_metrics")
async def shutdown_metrics():
    """Get shutdown metrics and monitoring data."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    try:
        current_status = shutdown_monitor.get_current_status()
        metrics_summary = shutdown_monitor.get_metrics_summary()
        recent_metrics = shutdown_monitor.get_recent_metrics(count=5)
        
        return {
            "timestamp": time.time(),
            "request_id": req_id,
            "correlation_id": corr_id,
            "current_status": current_status,
            "metrics_summary": metrics_summary,
            "recent_metrics": recent_metrics
        }
        
    except Exception as e:
        logger.error(
            "Shutdown metrics check failed",
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "error": str(e),
                "operation": "shutdown_metrics"
            }
        )
        
        raise HTTPException(status_code=500, detail="Failed to retrieve shutdown metrics")


# Root endpoint
@app.get("/api/v1/", tags=["📄 Project Summary"])
async def root():
    """Root endpoint with API information."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Root endpoint accessed",
        extra={
            "request_id": req_id,
            "correlation_id": corr_id,
            "operation": "root_access"
        }
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
    responses={404: {"description": "Not found"}}
)

app.include_router(
    analysis.router,
    prefix="/api/v1",
    responses={404: {"description": "Not found"}}
)

app.include_router(
    visualizations.router,
    prefix="/api/v1",
    responses={404: {"description": "Not found"}}
)


# API information endpoint
@app.get("/api/v1/info", tags=["📄 Project Summary"])
async def api_info():
    """Get comprehensive API information and capabilities."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "API info requested",
        extra={
            "request_id": req_id,
            "correlation_id": corr_id,
            "operation": "api_info"
        }
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
            },
            "users": {
                "count": 8,
                "base_path": "/api/v1/user",
                "operations": ["register", "login", "verify", "profile", "management"]
            }
        },
        "features": {
            "file_upload": True,
            "background_processing": True,
            "real_time_monitoring": True,
            "batch_operations": True,
            "search_and_filtering": True,
            "health_monitoring": True,
            "user_authentication": True,
            "otp_verification": True
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
        extra={
            "request_id": req_id,
            "correlation_id": corr_id,
            "operation": "api_info"
        }
    )
    
    return api_info


# Metrics endpoint for monitoring
@app.get("/api/v1/metrics", tags=["🔧 Setup, Data Loading, and System Monitoring"])
@monitor_performance("metrics_endpoint")
async def get_metrics():
    """Get API metrics and performance statistics."""
    
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    logger.info(
        "Metrics requested",
        extra={
            "request_id": req_id,
            "correlation_id": corr_id,
            "operation": "metrics_endpoint"
        }
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
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "operation": "metrics_endpoint"
            }
        )
        
        return metrics
        
    except Exception as e:
        logger.error(
            "Metrics retrieval failed",
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "error": str(e),
                "operation": "metrics_endpoint"
            }
        )
        
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


############################################################
# USER API ENDPOINTS
############################################################

@app.post("/api/v1/user/send-verification", response_model=VerificationResponse, tags=["🔧 Setup, Data Loading, and System Monitoring"])
async def send_verification(verification_request: VerificationRequest):
    """Send verification code to user via email or WhatsApp."""
    
    try:
        # Find user by email or phone
        user = None
        if verification_request.email:
            user = UserService.get_user_by_email(verification_request.email)
        elif verification_request.phone:
            user = UserService.get_user_by_phone(verification_request.phone)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found. Please register first.")
        
        if user["is_deleted"]:
            raise HTTPException(status_code=400, detail="Account has been deleted")
        
        # Generate and send OTP based on verification type
        if verification_request.verification_type == "email":
            if not verification_request.email:
                raise HTTPException(status_code=400, detail="Email is required for email verification")
            
            otp = UserService.create_otp(user["user_id"], email=verification_request.email)
            UserService.send_email_notification(user, "account_verification", otp=otp)

            return {
                "message": f"Verification code sent to {verification_request.email}",
                "expires_in": 5 * 60,  # 5 minutes
                "verification_type": "email"
            }
            
        elif verification_request.verification_type == "whatsapp":
            if not verification_request.phone:
                raise HTTPException(status_code=400, detail="Phone number is required for WhatsApp verification")
            
            otp = UserService.create_otp(user["user_id"], phone=verification_request.phone)
            UserService.send_whatsapp_notification(user, "account_verification", otp=otp)

            return {
                "message": f"Verification code sent to {verification_request.phone}",
                "expires_in": 5 * 60,  # 5 minutes
                "verification_type": "whatsapp"
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid verification type")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send verification endpoint: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/v1/user/register", response_model=UserResponseWithId, tags=["🔧 Setup, Data Loading, and System Monitoring"])
async def register_user(user_data: UserRegistration):
    """Register a new user with email OTP verification."""
    
    try:
        # Create user (unverified initially)
        user = UserService.create_user(
            full_name=user_data.full_name,
            email=user_data.email,
            phone=user_data.phone
        )
        
        # Generate and send email OTP for verification
        otp = UserService.create_otp(user["user_id"], email=user_data.email)
        UserService.send_email_notification(user, "account_verification", otp=otp)
        
        return {
            "user_id": user["user_id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "phone": user["phone"],
            "role": user.get("role", "user"),
            "message": "Registration successful. Please check your email for verification OTP."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in user registration endpoint: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/v1/user/login", tags=["🔧 Setup, Data Loading, and System Monitoring"])
async def login(login_data: UserLoginRequest):
    """Request OTP for email login."""
    
    try:
        user = UserService.get_user_by_email(login_data.email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found. Please register first.")
        
        if user["is_deleted"]:
            raise HTTPException(status_code=400, detail="Account has been deleted")
        
        if not user["is_verified"]:
            raise HTTPException(status_code=400, detail="Account not verified. Please verify your account first.")
        
        # Generate and send OTP for login
        otp = UserService.create_otp(user["user_id"], email=login_data.email)
        UserService.send_email_notification(user, "login_otp", otp=otp)
        
        return {
            "message": f"OTP sent to {login_data.email}",
            "expires_in": 5 * 60  # 5 minutes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login endpoint: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/v1/user/verify-registration", response_model=TokenResponse, tags=["🔧 Setup, Data Loading, and System Monitoring"])
async def verify_registration(request: VerifyOTPRequest):
    """Verify registration OTP and activate account."""
    return await verify_otp_and_generate_token(request, mark_verified=True)


@app.post("/api/v1/user/verify-login", response_model=TokenResponse, tags=["🔧 Setup, Data Loading, and System Monitoring"])
async def verify_login(request: VerifyOTPRequest):
    """Verify login OTP and generate access token."""
    return await verify_otp_and_generate_token(request, mark_verified=False)


@app.get("/api/v1/user/me", response_model=UserResponseWithFaces, summary="Get current user information", tags=["🔧 Setup, Data Loading, and System Monitoring"])
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user's information."""
    try:
        # Return user data
        return {
            "user_id": current_user["user_id"],
            "full_name": current_user["full_name"],
            "email": current_user["email"],
            "phone": current_user["phone"],
            "faces": []  # No face recognition in this version
        }
        
    except Exception as e:
        logger.error(f"Error fetching user information: {e}")
        logger.error(traceback.format_exc())
        # Return basic user info in case of error
        return {
            "user_id": current_user["user_id"],
            "full_name": current_user["full_name"],
            "email": current_user["email"],
            "phone": current_user["phone"],
            "faces": []
        }


@app.get("/api/v1/diagram", tags=["📄 Project Summary"])
async def get_architecture_diagram(format: str = "svg", background_tasks: BackgroundTasks = BackgroundTasks()):
    """Generate the architecture diagram (Mermaid) and return as a file (SVG/PNG).
    Requires mermaid-cli (mmdc) available in PATH.
    """
    req_id = request_id.get()
    corr_id = correlation_id.get()

    mermaid = (
        "flowchart LR\n"
        "  subgraph Clients\n"
        "    A1[NOTEBOOK\\npollinexus-done.ipynb]\n"
        "    A2[cURL/HTTP Tools\\n(API.md steps)]\n"
        "    A3[Makefile\\nmake run-local|run-docker|run-remote]\n"
        "  end\n\n"
        "  subgraph API Layer (FastAPI)\n"
        "    B1[FastAPI App\\n/health /info /metrics]\n"
        "    B2[Routers\\nDatasets / Analysis / Visualizations / User]\n"
        "    B3[Models & Validation\\nPydantic]\n"
        "    B4[Middleware\\nSecurity, CORS, Logging, Errors]\n"
        "  end\n\n"
        "  subgraph Services (Domain Logic)\n"
        "    C1[Dataset Service\\nvalidate, profile, checksum]\n"
        "    C2[Analysis Service\\nbee prefs, recs,\\nseasonal, site compare]\n"
        "    C3[Visualization Service\\nplots, dashboard]\n"
        "    C4[User Service\\nregister, OTP, JWT]\n"
        "  end\n\n"
        "  subgraph Background Tasks\n"
        "    D1[Celery Workers\\nasync jobs]\n"
        "    D2[Task Routing & Monitoring]\n"
        "  end\n\n"
        "  subgraph Data Layer\n"
        "    E1[(DuckDB)\\nanalytics + CRUD]\n"
        "    E2[(Filesystem)\\nuploads / visualizations]\n"
        "    E3[(Redis)\\nstatus, ephemeral]\n"
        "  end\n\n"
        "  subgraph Observability\n"
        "    F1[Health & Detailed Health]\n"
        "    F2[Metrics]\n"
        "    F3[Structured Logging\\ncorrelation_id / request_id]\n"
        "    F4[Security Status]\n"
        "  end\n\n"
        "  A1 -->|interactive cells| B1\n"
        "  A2 -->|HTTP requests| B1\n"
        "  A3 -->|run targets| B1\n\n"
        "  B1 --> B4\n"
        "  B1 --> B2\n"
        "  B2 --> B3\n"
        "  B2 -->|datasets| C1\n"
        "  B2 -->|analysis| C2\n"
        "  B2 -->|visualizations| C3\n"
        "  B2 -->|user| C4\n\n"
        "  C2 -->|enqueue| D1\n"
        "  C3 -->|enqueue| D1\n"
        "  D1 --> D2\n\n"
        "  C1 --> E1\n"
        "  C1 --> E2\n"
        "  C2 --> E1\n"
        "  C3 --> E1\n"
        "  C3 --> E2\n"
        "  D1 --> E3\n\n"
        "  D2 -->|job status| B1\n"
        "  E3 -->|task status| B1\n"
        "  E2 -->|download link| B1\n\n"
        "  B1 --> F1\n"
        "  B1 --> F2\n"
        "  B1 --> F3\n"
        "  B1 --> F4\n"
    )

    fmt = (format or "svg").lower()
    if fmt not in {"svg", "png"}:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'svg' or 'png'.")

    # Preferred: Python renderer (mermaid-py)
    if mermaid_py is not None:
        try:
            logger.info(
                "Rendering diagram using mermaid-py",
                extra={
                    "request_id": req_id,
                    "correlation_id": corr_id,
                    "operation": "mermaid_py_render",
                    "component": "project_summary",
                    "format": fmt,
                },
            )
            svg_content = None
            # Try common APIs for mermaid-py
            try:
                svg_content = mermaid_py.Mermaid(mermaid).render()
            except Exception:
                try:
                    # Some variants expose a functional render
                    svg_content = mermaid_py.render(mermaid)
                except Exception as e:
                    logger.error(
                        "mermaid-py render failed",
                        extra={
                            "request_id": req_id,
                            "correlation_id": corr_id,
                            "error": str(e),
                        },
                    )
                    svg_content = None

            if not svg_content:
                raise RuntimeError("mermaid-py did not return SVG content")

            with tempfile.TemporaryDirectory() as tmpdir:
                if fmt == "svg":
                    final_dir = tempfile.mkdtemp()
                    final_path = os.path.join(final_dir, "pollinexus_architecture.svg")
                    with open(final_path, "w", encoding="utf-8") as fsvg:
                        fsvg.write(svg_content)
                    media_type = "image/svg+xml"
                else:  # png
                    if cairosvg is None:
                        raise HTTPException(
                            status_code=501,
                            detail=(
                                "cairosvg not available for PNG conversion. Install with: pip install cairosvg"
                            ),
                        )
                    # Convert SVG -> PNG
                    final_dir = tempfile.mkdtemp()
                    final_path = os.path.join(final_dir, "pollinexus_architecture.png")
                    cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to=final_path)
                    media_type = "image/png"

                filename = os.path.basename(final_path)

                def _cleanup(path: str, dirpath: str):
                    try:
                        if os.path.exists(path):
                            os.remove(path)
                        if os.path.isdir(dirpath):
                            shutil.rmtree(dirpath, ignore_errors=True)
                    except Exception as e:
                        logger.warning(
                            "Failed to cleanup temp diagram files",
                            extra={
                                "request_id": req_id,
                                "correlation_id": corr_id,
                                "error": str(e),
                            },
                        )

                background_tasks.add_task(_cleanup, final_path, final_dir)

                logger.info(
                    "Diagram generated successfully (mermaid-py)",
                    extra={
                        "request_id": req_id,
                        "correlation_id": corr_id,
                        "operation": "mermaid_py_render",
                        "component": "project_summary",
                        "format": fmt,
                        "file": filename,
                    },
                )
                return FileResponse(path=final_path, media_type=media_type, filename=filename)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during mermaid-py rendering; will attempt mmdc fallback",
                extra={
                    "request_id": req_id,
                    "correlation_id": corr_id,
                    "operation": "mermaid_py_render_error",
                    "error": str(e),
                },
            )
    else:
        logger.info(
            "mermaid-py not available; will attempt mmdc fallback",
            extra={
                "request_id": req_id,
                "correlation_id": corr_id,
                "operation": "mermaid_py_missing",
            },
        )

    # Fallback: mmdc (Node CLI)
    mmdc_path = shutil.which("mmdc")
    if not mmdc_path:
        # Attempt auto-install in development only
        if settings.is_development:
            npm_path = shutil.which("npm")
            if npm_path:
                try:
                    logger.warning(
                        "Mermaid CLI not found. Attempting npm global install (@mermaid-js/mermaid-cli)",
                        extra={
                            "request_id": req_id,
                            "correlation_id": corr_id,
                            "operation": "mmdc_auto_install",
                            "component": "project_summary",
                        },
                    )
                    npm_bin_proc = subprocess.run(
                        [npm_path, "bin", "-g"], capture_output=True, text=True, timeout=20
                    )
                    npm_bin_dir = npm_bin_proc.stdout.strip() if npm_bin_proc.returncode == 0 else ""
                    install_proc = subprocess.run(
                        [npm_path, "i", "-g", "@mermaid-js/mermaid-cli"],
                        capture_output=True,
                        text=True,
                        timeout=180,
                    )
                    if install_proc.returncode == 0 and npm_bin_dir and os.path.isdir(npm_bin_dir):
                        os.environ["PATH"] = npm_bin_dir + os.pathsep + os.environ.get("PATH", "")
                    else:
                        logger.error(
                            "npm install of mermaid-cli failed",
                            extra={
                                "request_id": req_id,
                                "correlation_id": corr_id,
                                "stderr": install_proc.stderr if install_proc else None,
                                "stdout": install_proc.stdout if install_proc else None,
                            },
                        )
                except Exception as e:
                    logger.error(
                        "Unexpected error during mermaid-cli auto-install",
                        extra={
                            "request_id": req_id,
                            "correlation_id": corr_id,
                            "operation": "mmdc_auto_install_error",
                            "error": str(e),
                        },
                    )
        mmdc_path = shutil.which("mmdc")
        if not mmdc_path:
            raise HTTPException(
                status_code=501,
                detail=(
                    "Mermaid renderer not available. Install Python mermaid-py (pip install mermaid-py)"
                    " or Node mmdc (@mermaid-js/mermaid-cli)."
                ),
            )

    # Existing mmdc rendering block remains unchanged below
    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = os.path.join(tmpdir, "diagram.mmd")
        out_path = os.path.join(tmpdir, f"diagram.{fmt}")
        try:
            with open(src_path, "w", encoding="utf-8") as f:
                f.write(mermaid)
            cmd = [mmdc_path, "-i", src_path, "-o", out_path]
            cmd += ["-e", fmt]
            logger.info(
                "Generating diagram via mermaid-cli",
                extra={
                    "request_id": req_id,
                    "correlation_id": corr_id,
                    "operation": "mmdc_render",
                    "component": "project_summary",
                    "format": fmt,
                },
            )
            completed = subprocess.run(cmd, cwd=tmpdir, timeout=30, capture_output=True, text=True)
            if completed.returncode != 0 or not os.path.exists(out_path):
                logger.error(
                    "Diagram generation failed",
                    extra={
                        "request_id": req_id,
                        "correlation_id": corr_id,
                        "stderr": completed.stderr,
                        "stdout": completed.stdout,
                        "operation": "mmdc_render",
                        "format": fmt,
                    },
                )
                raise HTTPException(status_code=500, detail="Failed to generate diagram")
            final_dir = tempfile.mkdtemp()
            final_path = os.path.join(final_dir, f"pollinexus_architecture.{fmt}")
            shutil.move(out_path, final_path)
            media_type = "image/svg+xml" if fmt == "svg" else "image/png"
            filename = os.path.basename(final_path)
            def _cleanup(path: str, dirpath: str):
                try:
                    if os.path.exists(path):
                        os.remove(path)
                    if os.path.isdir(dirpath):
                        shutil.rmtree(dirpath, ignore_errors=True)
                except Exception as e:
                    logger.warning(
                        "Failed to cleanup temp diagram files",
                        extra={
                            "request_id": req_id,
                            "correlation_id": corr_id,
                            "error": str(e),
                        },
                    )
            background_tasks.add_task(_cleanup, final_path, final_dir)
            logger.info(
                "Diagram generated successfully",
                extra={
                    "request_id": req_id,
                    "correlation_id": corr_id,
                    "operation": "mmdc_render",
                    "component": "project_summary",
                    "format": fmt,
                    "file": filename,
                },
            )
            return FileResponse(path=final_path, media_type=media_type, filename=filename)
        except subprocess.TimeoutExpired:
            logger.error(
                "Diagram generation timed out",
                extra={
                    "request_id": req_id,
                    "correlation_id": corr_id,
                    "operation": "mmdc_render_timeout",
                    "format": fmt,
                },
            )
            raise HTTPException(status_code=504, detail="Diagram generation timed out")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during diagram generation",
                extra={
                    "request_id": req_id,
                    "correlation_id": corr_id,
                    "operation": "mmdc_render_error",
                    "error": str(e),
                },
            )
            raise HTTPException(status_code=500, detail="Unexpected error during diagram generation")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "pollinexus.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    ) 