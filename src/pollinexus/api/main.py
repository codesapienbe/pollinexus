"""
Main FastAPI application for Pollinexus API.

This module configures the FastAPI application with all routes,
middleware, and error handling.
"""

from fastapi import FastAPI, Request, HTTPException, Depends, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uuid
import traceback
from typing import Dict, Any

from ..core.config import settings
from ..core.logging import logger, request_id, correlation_id
from ..core.metrics import monitor_performance
from ..core.error_tracking import track_errors, error_tracker
from ..core.auth import get_current_user, verify_otp_and_generate_token
from ..core.security import create_security_middleware, security_monitor
from ..core.health import health_monitor, get_health_status, get_quick_health
from ..services.user_service import UserService
from .routes import datasets, analysis, visualizations
from .models.user_models import (
    UserRegistration, UserLoginRequest, VerifyOTPRequest, VerificationRequest,
    UserResponseWithId, TokenResponse, VerificationResponse, UserResponseWithFaces
)


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
    
    yield
    
    # Shutdown
    logger.info(
        "Pollinexus API shutting down",
        extra={"operation": "app_shutdown"}
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

# Add Security middleware (must be first)
app.add_middleware(create_security_middleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add TrustedHost middleware
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
@app.get("/api/v1/health", tags=["Health API"])
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


@app.get("/api/v1/health/detailed", tags=["Health API"])
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


@app.get("/api/v1/security/status", tags=["Security API"])
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


# Root endpoint
@app.get("/api/v1/", tags=["Root API"])
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
@app.get("/api/v1/info", tags=["API Info API"])
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
                "base_path": "/user",
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
@app.get("/api/v1/metrics", tags=["Monitoring API"])
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

@app.post("/user/send-verification", response_model=VerificationResponse, tags=["User API"])
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


@app.post("/user/register", response_model=UserResponseWithId, tags=["User API"])
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


@app.post("/user/login", tags=["User API"])
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


@app.post("/user/verify-registration", response_model=TokenResponse, tags=["User API"])
async def verify_registration(request: VerifyOTPRequest):
    """Verify registration OTP and activate account."""
    return await verify_otp_and_generate_token(request, mark_verified=True)


@app.post("/user/verify-login", response_model=TokenResponse, tags=["User API"])
async def verify_login(request: VerifyOTPRequest):
    """Verify login OTP and generate access token."""
    return await verify_otp_and_generate_token(request, mark_verified=False)


@app.get("/api/v1/user/me", response_model=UserResponseWithFaces, summary="Get current user information", tags=["User API"])
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


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "pollinexus.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    ) 