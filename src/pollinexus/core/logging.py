"""
Logging configuration for Pollinexus API.

This module provides structured logging with OpenTelemetry compatibility,
correlation IDs, and comprehensive monitoring capabilities.
"""

import logging
import json
import sys
import time
import re
from typing import Any, Dict, Optional, Set
from contextvars import ContextVar
import uuid
from datetime import datetime

# Context variables for request tracking
request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)

# Sensitive data patterns for sanitization
SENSITIVE_PATTERNS = {
    'password': r'password["\']?\s*[:=]\s*["\']?[^"\s,}]+',
    'token': r'token["\']?\s*[:=]\s*["\']?[^"\s,}]+',
    'api_key': r'api[_-]?key["\']?\s*[:=]\s*["\']?[^"\s,}]+',
    'secret': r'secret["\']?\s*[:=]\s*["\']?[^"\s,}]+',
    'authorization': r'authorization["\']?\s*[:=]\s*["\']?bearer\s+[^"\s,}]+',
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'credit_card': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
    'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
}

# Fields that should always be sanitized
SENSITIVE_FIELDS = {
    'password', 'token', 'api_key', 'secret', 'authorization', 
    'email', 'phone', 'ssn', 'credit_card', 'ip_address',
    'client_secret', 'access_token', 'refresh_token', 'private_key',
    'session_id', 'cookie', 'auth_token', 'jwt_token'
}

def sanitize_sensitive_data(data: Any) -> Any:
    """Recursively sanitize sensitive data from log entries."""
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            # Check if key contains sensitive terms
            key_lower = key.lower()
            is_sensitive_key = any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS)
            
            if is_sensitive_key:
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = sanitize_sensitive_data(value)
        return sanitized
    
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    
    elif isinstance(data, str):
        # Apply pattern-based sanitization
        sanitized = data
        for pattern_name, pattern in SENSITIVE_PATTERNS.items():
            if pattern_name in ['email', 'phone', 'ssn', 'credit_card']:
                # Replace with masked version
                sanitized = re.sub(pattern, f'[{pattern_name.upper()}_REDACTED]', sanitized)
            else:
                # Replace with generic redaction
                sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        return sanitized
    
    else:
        return data


class StructuredJSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging with OpenTelemetry compatibility."""
    
    def __init__(self, sanitize_sensitive: bool = True):
        super().__init__()
        self.sanitize_sensitive = sanitize_sensitive
    
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
        
        # Sanitize sensitive data if enabled
        if self.sanitize_sensitive:
            log_entry = sanitize_sensitive_data(log_entry)
        
        try:
            return json.dumps(log_entry, default=str, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            # Fallback to safe JSON serialization
            fallback_entry = {
                "timestamp": log_entry.get("timestamp", datetime.utcnow().isoformat() + "Z"),
                "level": log_entry.get("level", "ERROR"),
                "logger": log_entry.get("logger", "pollinexus"),
                "message": f"Log serialization error: {str(e)}",
                "original_message": str(log_entry.get("message", "")),
                "serialization_error": str(e)
            }
            return json.dumps(fallback_entry, ensure_ascii=False)


class CustomLogger(logging.Logger):
    """Logger that safely accepts arbitrary keyword args and merges them into extra."""

    def _merge_extra(self, extra: Optional[Dict[str, Any]], kwargs: Dict[str, Any]) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}
        if extra:
            merged.update(extra)
        if kwargs:
            merged.update(kwargs)
        # Drop None-valued fields to keep logs clean
        return {k: v for k, v in merged.items() if v is not None}

    def debug(self, msg, *args, extra=None, **kwargs):
        return super().debug(msg, *args, extra=self._merge_extra(extra, kwargs))

    def info(self, msg, *args, extra=None, **kwargs):
        return super().info(msg, *args, extra=self._merge_extra(extra, kwargs))

    def warning(self, msg, *args, extra=None, **kwargs):
        return super().warning(msg, *args, extra=self._merge_extra(extra, kwargs))

    def error(self, msg, *args, extra=None, **kwargs):
        return super().error(msg, *args, extra=self._merge_extra(extra, kwargs))

    def critical(self, msg, *args, extra=None, **kwargs):
        return super().critical(msg, *args, extra=self._merge_extra(extra, kwargs))

    def exception(self, msg, *args, extra=None, **kwargs):
        # Keep stack info via exc_info=True if not provided
        if 'exc_info' not in kwargs:
            kwargs['exc_info'] = True
        return super().error(msg, *args, extra=self._merge_extra(extra, kwargs), exc_info=kwargs.get('exc_info'))

    def log(self, level, msg, *args, extra=None, **kwargs):
        return super().log(level, msg, *args, extra=self._merge_extra(extra, kwargs))


# Ensure our custom logger is used globally before any loggers are created
logging.setLoggerClass(CustomLogger)


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    include_timestamp: bool = True,
    include_correlation_id: bool = True,
    sanitize_sensitive: bool = True
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
        formatter = StructuredJSONFormatter(sanitize_sensitive=sanitize_sensitive)
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Create file handler for application logs with rotation
    try:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            "application.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
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


class LogMonitor:
    """Monitor for log aggregation and alerting."""
    
    def __init__(self):
        self.error_counts = {}
        self.warning_counts = {}
        self.performance_metrics = {}
        self.alert_thresholds = {
            'error_rate': 0.1,  # 10% error rate threshold
            'response_time': 5.0,  # 5 seconds response time threshold
            'memory_usage': 0.8,  # 80% memory usage threshold
            'concurrent_requests': 100  # 100 concurrent requests threshold
        }
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5 minutes between alerts
    
    def record_error(self, error_type: str, context: Optional[Dict[str, Any]] = None):
        """Record an error for monitoring."""
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
        
        # Check if we should alert
        self._check_error_threshold(error_type)
    
    def record_warning(self, warning_type: str, context: Optional[Dict[str, Any]] = None):
        """Record a warning for monitoring."""
        if warning_type not in self.warning_counts:
            self.warning_counts[warning_type] = 0
        self.warning_counts[warning_type] += 1
    
    def record_performance(self, operation: str, execution_time: float, 
                          memory_delta: float = 0, cpu_usage: float = 0):
        """Record performance metrics."""
        if operation not in self.performance_metrics:
            self.performance_metrics[operation] = {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
                'max_time': 0,
                'min_time': float('inf'),
                'memory_delta': 0,
                'cpu_usage': 0
            }
        
        metrics = self.performance_metrics[operation]
        metrics['count'] += 1
        metrics['total_time'] += execution_time
        metrics['avg_time'] = metrics['total_time'] / metrics['count']
        metrics['max_time'] = max(metrics['max_time'], execution_time)
        metrics['min_time'] = min(metrics['min_time'], execution_time)
        metrics['memory_delta'] += memory_delta
        metrics['cpu_usage'] = max(metrics['cpu_usage'], cpu_usage)
        
        # Check performance thresholds
        self._check_performance_threshold(operation, execution_time)
    
    def _check_error_threshold(self, error_type: str):
        """Check if error rate exceeds threshold."""
        current_time = time.time()
        alert_key = f"error_{error_type}"
        
        # Check cooldown
        if alert_key in self.last_alert_time:
            if current_time - self.last_alert_time[alert_key] < self.alert_cooldown:
                return
        
        # Calculate error rate (simplified - in production, use time windows)
        total_errors = sum(self.error_counts.values())
        if total_errors > 10:  # Only alert after minimum threshold
            error_rate = self.error_counts[error_type] / total_errors
            if error_rate > self.alert_thresholds['error_rate']:
                logger.critical(
                    f"High error rate detected for {error_type}",
                    extra={
                        "alert_type": "high_error_rate",
                        "error_type": error_type,
                        "error_rate": error_rate,
                        "threshold": self.alert_thresholds['error_rate'],
                        "total_errors": total_errors
                    }
                )
                self.last_alert_time[alert_key] = current_time
    
    def _check_performance_threshold(self, operation: str, execution_time: float):
        """Check if performance exceeds threshold."""
        current_time = time.time()
        alert_key = f"performance_{operation}"
        
        # Check cooldown
        if alert_key in self.last_alert_time:
            if current_time - self.last_alert_time[alert_key] < self.alert_cooldown:
                return
        
        if execution_time > self.alert_thresholds['response_time']:
            logger.warning(
                f"Slow operation detected: {operation}",
                extra={
                    "alert_type": "slow_operation",
                    "operation": operation,
                    "execution_time": execution_time,
                    "threshold": self.alert_thresholds['response_time']
                }
            )
            self.last_alert_time[alert_key] = current_time
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        return {
            "error_counts": self.error_counts.copy(),
            "warning_counts": self.warning_counts.copy(),
            "performance_metrics": self.performance_metrics.copy(),
            "alert_thresholds": self.alert_thresholds.copy()
        }
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing or periodic resets)."""
        self.error_counts.clear()
        self.warning_counts.clear()
        self.performance_metrics.clear()
        self.last_alert_time.clear()


# Global log monitor instance
log_monitor = LogMonitor()


def log_with_monitoring(level: str, message: str, context: Optional[Dict[str, Any]] = None,
                       monitor_errors: bool = True, monitor_performance: bool = False,
                       execution_time: float = 0, memory_delta: float = 0, cpu_usage: float = 0):
    """Log message with monitoring capabilities."""
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    log_data = {
        "request_id": req_id,
        "correlation_id": corr_id
    }
    
    if context:
        log_data.update(context)
    
    # Log the message
    getattr(logger, level.lower())(message, extra=log_data)
    
    # Monitor errors
    if monitor_errors and level.upper() in ['ERROR', 'CRITICAL']:
        error_type = context.get('error_type', 'unknown') if context else 'unknown'
        log_monitor.record_error(error_type, context)
    
    # Monitor warnings
    if level.upper() == 'WARNING':
        warning_type = context.get('warning_type', 'unknown') if context else 'unknown'
        log_monitor.record_warning(warning_type, context)
    
    # Monitor performance
    if monitor_performance and execution_time > 0:
        operation = context.get('operation', 'unknown') if context else 'unknown'
        log_monitor.record_performance(operation, execution_time, memory_delta, cpu_usage)


# Enhanced performance decorator with monitoring
def log_performance_with_monitoring(operation: str, alert_threshold: float = 5.0):
    """Enhanced decorator to log function performance with monitoring."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            req_id = request_id.get()
            corr_id = correlation_id.get()
            
            logger.info(
                f"Starting {operation}",
                extra={
                    "operation": operation,
                    "function": func.__name__,
                    "request_id": req_id,
                    "correlation_id": corr_id
                }
            )
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log completion with monitoring
                log_with_monitoring(
                    "INFO",
                    f"Completed {operation}",
                    context={
                        "operation": operation,
                        "function": func.__name__,
                        "execution_time": execution_time,
                        "request_id": req_id,
                        "correlation_id": corr_id
                    },
                    monitor_performance=True,
                    execution_time=execution_time
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Log error with monitoring
                log_with_monitoring(
                    "ERROR",
                    f"Failed {operation}",
                    context={
                        "operation": operation,
                        "function": func.__name__,
                        "execution_time": execution_time,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "request_id": req_id,
                        "correlation_id": corr_id
                    },
                    monitor_errors=True
                )
                
                raise
        
        return wrapper
    return decorator


# Utility function to get monitoring metrics
def get_monitoring_metrics() -> Dict[str, Any]:
    """Get current monitoring metrics."""
    return log_monitor.get_metrics_summary()


# Utility function to reset monitoring metrics
def reset_monitoring_metrics():
    """Reset monitoring metrics."""
    log_monitor.reset_metrics() 