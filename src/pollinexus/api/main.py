"""
Main FastAPI application for Pollinexus.

This module initializes the FastAPI application with all necessary middleware,
routers, and configuration.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from .routes import datasets, analysis, visualizations
from ..core.config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Pollinexus API",
    description="Data-Driven Pollinator Conservation API for Environmental Agencies",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://pollinex.us"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "pollinex.us",
            "api.pollinex.us",
            "localhost",
            "127.0.0.1",
            "host.docker.internal"
        ]
    )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )


# Include routers
app.include_router(
    datasets.router,
    prefix="/api/v1",
    tags=["datasets"],
    responses={404: {"description": "Not found"}},
)

app.include_router(
    analysis.router,
    prefix="/api/v1",
    tags=["analysis"],
    responses={404: {"description": "Not found"}},
)

app.include_router(
    visualizations.router,
    prefix="/api/v1",
    tags=["visualizations"],
    responses={404: {"description": "Not found"}},
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to Pollinexus API",
        "version": "0.1.0",
        "description": "Data-Driven Pollinator Conservation API",
        "docs": "/docs" if settings.debug else None,
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "0.1.0"
    }


@app.get("/api/v1/health")
async def api_health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "api_version": "v1",
        "timestamp": time.time()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "pollinexus.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 