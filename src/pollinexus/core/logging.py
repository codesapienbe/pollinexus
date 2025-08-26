"""
Logging configuration for Pollinexus API.

This module provides structured logging with OpenTelemetry compatibility,
correlation IDs, and comprehensive monitoring capabilities.
"""

import logging
import json
import sys
import time
from typing import Any, Dict, Optional
from contextvars import ContextVar
import uuid
from datetime import datetime

# Context variables for request tracking
request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class StructuredJSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging with OpenTelemetry compatibility."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        
        # Base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add context variables if available
        if request_id.get():
            log_entry["request_id"] = request_id.get()
        if correlation_id.get():
            log_entry["correlation_id"] = correlation_id.get()
        if user_id.get():
            log_entry["user_id"] = user_id.get()
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    include_timestamp: bool = True,
    include_correlation_id: bool = True
) -> None:
    """Setup logging configuration with structured formatting."""
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Set formatter based on type
    if format_type.lower() == "json":
        formatter = StructuredJSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Create file handler for application logs
    try:
        file_handler = logging.FileHandler("application.log")
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        # Log to console if file logging fails
        console_handler.setFormatter(logging.Formatter(
            f'%(asctime)s - %(name)s - %(levelname)s - %(message)s (File logging failed: {e})'
        ))


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)


# Setup default logging
setup_logging()

# Create main application logger
logger = get_logger("pollinexus")


class LogContext:
    """Context manager for adding context to log entries."""
    
    def __init__(self, **kwargs):
        self.context = kwargs
        self.previous_context = {}
    
    def __enter__(self):
        # Store previous context
        for key, value in self.context.items():
            if hasattr(logging, key):
                self.previous_context[key] = getattr(logging, key)
                setattr(logging, key, value)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous context
        for key, value in self.previous_context.items():
            setattr(logging, key, value)


def log_with_context(logger_instance: logging.Logger, level: str, message: str, **kwargs):
    """Log message with additional context."""
    extra_data = {
        "request_id": request_id.get(),
        "correlation_id": correlation_id.get(),
        "user_id": user_id.get(),
        **kwargs
    }
    
    # Remove None values
    extra_data = {k: v for k, v in extra_data.items() if v is not None}
    
    getattr(logger_instance, level.lower())(message, extra=extra_data)


def set_request_context(req_id: Optional[str] = None, corr_id: Optional[str] = None, 
                       user_id_val: Optional[str] = None):
    """Set request context variables."""
    if req_id:
        request_id.set(req_id)
    if corr_id:
        correlation_id.set(corr_id)
    if user_id_val:
        user_id.set(user_id_val)


def clear_request_context():
    """Clear request context variables."""
    request_id.set(None)
    correlation_id.set(None)
    user_id.set(None)


def generate_correlation_id() -> str:
    """Generate a unique correlation ID."""
    return str(uuid.uuid4())


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


# Performance monitoring decorator
def log_performance(operation: str):
    """Decorator to log function performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            req_id = request_id.get()
            corr_id = correlation_id.get()
            
            logger.info(
                f"Starting {operation}",
                operation=operation,
                function=func.__name__,
                request_id=req_id,
                correlation_id=corr_id
            )
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.info(
                    f"Completed {operation}",
                    operation=operation,
                    function=func.__name__,
                    execution_time=execution_time,
                    request_id=req_id,
                    correlation_id=corr_id
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                logger.error(
                    f"Failed {operation}",
                    operation=operation,
                    function=func.__name__,
                    execution_time=execution_time,
                    error=str(e),
                    request_id=req_id,
                    correlation_id=corr_id
                )
                
                raise
        
        return wrapper
    return decorator


# Error logging utilities
def log_error(error: Exception, context: Optional[Dict[str, Any]] = None, 
              level: str = "ERROR"):
    """Log an error with context."""
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "request_id": req_id,
        "correlation_id": corr_id
    }
    
    if context:
        error_data.update(context)
    
    getattr(logger, level.lower())(
        f"Error occurred: {error}",
        extra=error_data
    )


def log_warning(message: str, context: Optional[Dict[str, Any]] = None):
    """Log a warning with context."""
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    warning_data = {
        "request_id": req_id,
        "correlation_id": corr_id
    }
    
    if context:
        warning_data.update(context)
    
    logger.warning(message, extra=warning_data)


def log_info(message: str, context: Optional[Dict[str, Any]] = None):
    """Log an info message with context."""
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    info_data = {
        "request_id": req_id,
        "correlation_id": corr_id
    }
    
    if context:
        info_data.update(context)
    
    logger.info(message, extra=info_data)


def log_debug(message: str, context: Optional[Dict[str, Any]] = None):
    """Log a debug message with context."""
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    debug_data = {
        "request_id": req_id,
        "correlation_id": corr_id
    }
    
    if context:
        debug_data.update(context)
    
    logger.debug(message, extra=debug_data) 