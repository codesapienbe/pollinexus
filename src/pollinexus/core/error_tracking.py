"""
Error tracking and alerting system for Pollinexus API.

This module provides comprehensive error tracking, categorization,
and alerting capabilities for monitoring application health.
"""

import time
import threading
from typing import Any, Dict, List, Optional, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json

from .logging import logger, request_id, correlation_id


@dataclass
class ErrorRecord:
    """Represents an error record with metadata."""
    error_type: str
    error_message: str
    timestamp: float
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    severity: str = "ERROR"
    stack_trace: Optional[str] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


class ErrorTracker:
    """Central error tracking and alerting system."""
    
    def __init__(self, max_errors: int = 10000, alert_threshold: int = 10):
        self.max_errors = max_errors
        self.alert_threshold = alert_threshold
        self.errors = deque(maxlen=max_errors)
        self.error_counts = defaultdict(int)
        self.alert_callbacks: List[Callable] = []
        self.lock = threading.Lock()
        self.initialized = False
        
        # Error categorization
        self.error_categories = {
            "api": ["api_request_error", "api_validation_error", "api_timeout"],
            "database": ["db_connection_error", "db_query_error", "db_timeout"],
            "celery": ["celery_task_error", "celery_timeout", "celery_connection_error"],
            "file": ["file_not_found", "file_permission_error", "file_corruption"],
            "validation": ["data_validation_error", "schema_validation_error"],
            "authentication": ["auth_error", "permission_denied", "token_expired"],
            "external": ["external_api_error", "network_error", "timeout"],
            "system": ["memory_error", "cpu_error", "disk_error"]
        }
    
    def initialize(self):
        """Initialize the error tracker."""
        with self.lock:
            if not self.initialized:
                logger.info("Error tracker initialized")
                self.initialized = True
    
    def track_error(self, error_type: str, error_message: str, 
                   context: Optional[Dict[str, Any]] = None, 
                   severity: str = "ERROR", stack_trace: Optional[str] = None):
        """Track an error with metadata."""
        with self.lock:
            error_record = ErrorRecord(
                error_type=error_type,
                error_message=error_message,
                timestamp=time.time(),
                request_id=request_id.get(),
                correlation_id=correlation_id.get(),
                context=context or {},
                severity=severity,
                stack_trace=stack_trace
            )
            
            # Add to error list
            self.errors.append(error_record)
            
            # Update error counts
            self.error_counts[error_type] += 1
            
            # Check for alerts
            self._check_alerts(error_type)
            
            # Log error
            logger.error(
                f"Error tracked: {error_type}",
                extra={
                    "error_type": error_type,
                    "error_message": error_message,
                    "severity": severity,
                    "request_id": error_record.request_id,
                    "correlation_id": error_record.correlation_id,
                    "context": context
                }
            )
    
    def _check_alerts(self, error_type: str):
        """Check if error count exceeds threshold and trigger alerts."""
        if self.error_counts[error_type] >= self.alert_threshold:
            self._trigger_alert(error_type, self.error_counts[error_type])
    
    def _trigger_alert(self, error_type: str, count: int):
        """Trigger an alert for high error count."""
        alert_data = {
            "error_type": error_type,
            "count": count,
            "threshold": self.alert_threshold,
            "timestamp": time.time(),
            "message": f"High error count for {error_type}: {count} errors"
        }
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
        
        # Log alert
        logger.warning(
            f"Error alert triggered: {error_type}",
            extra={
                "error_type": error_type,
                "count": count,
                "threshold": self.alert_threshold
            }
        )
    
    def add_alert_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add a callback function for error alerts."""
        self.alert_callbacks.append(callback)
    
    def get_error_summary(self, time_window: Optional[float] = None) -> Dict[str, Any]:
        """Get a summary of errors within a time window."""
        with self.lock:
            if time_window is None:
                # Use all errors
                recent_errors = list(self.errors)
            else:
                # Filter by time window
                cutoff_time = time.time() - time_window
                recent_errors = [
                    error for error in self.errors 
                    if error.timestamp >= cutoff_time
                ]
            
            # Categorize errors
            categorized_errors = defaultdict(int)
            severity_counts = defaultdict(int)
            
            for error in recent_errors:
                # Find category
                category = "unknown"
                for cat, types in self.error_categories.items():
                    if error.error_type in types:
                        category = cat
                        break
                
                categorized_errors[category] += 1
                severity_counts[error.severity] += 1
            
            return {
                "total_errors": len(recent_errors),
                "time_window": time_window,
                "categorized_errors": dict(categorized_errors),
                "severity_counts": dict(severity_counts),
                "error_types": dict(self.error_counts),
                "timestamp": time.time()
            }
    
    def get_recent_errors(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent error records."""
        with self.lock:
            recent_errors = list(self.errors)[-limit:]
            return [asdict(error) for error in recent_errors]
    
    def get_errors_by_type(self, error_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get errors of a specific type."""
        with self.lock:
            filtered_errors = [
                error for error in self.errors 
                if error.error_type == error_type
            ][-limit:]
            return [asdict(error) for error in filtered_errors]
    
    def get_errors_by_category(self, category: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get errors of a specific category."""
        with self.lock:
            if category not in self.error_categories:
                return []
            
            category_types = self.error_categories[category]
            filtered_errors = [
                error for error in self.errors 
                if error.error_type in category_types
            ][-limit:]
            return [asdict(error) for error in filtered_errors]
    
    def clear_errors(self, error_type: Optional[str] = None):
        """Clear errors, optionally by type."""
        with self.lock:
            if error_type:
                # Clear specific error type
                self.errors = deque(
                    [error for error in self.errors if error.error_type != error_type],
                    maxlen=self.max_errors
                )
                self.error_counts[error_type] = 0
            else:
                # Clear all errors
                self.errors.clear()
                self.error_counts.clear()
            
            logger.info(f"Errors cleared: {error_type or 'all'}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        with self.lock:
            if not self.errors:
                return {"total_errors": 0, "error_types": {}}
            
            # Calculate time-based stats
            now = time.time()
            last_hour = now - 3600
            last_day = now - 86400
            
            errors_last_hour = [e for e in self.errors if e.timestamp >= last_hour]
            errors_last_day = [e for e in self.errors if e.timestamp >= last_day]
            
            # Error rate calculations
            hourly_rate = len(errors_last_hour)
            daily_rate = len(errors_last_day)
            
            # Most common error types
            error_type_counts = defaultdict(int)
            for error in self.errors:
                error_type_counts[error.error_type] += 1
            
            most_common = sorted(
                error_type_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            
            return {
                "total_errors": len(self.errors),
                "errors_last_hour": hourly_rate,
                "errors_last_day": daily_rate,
                "hourly_rate": hourly_rate,
                "daily_rate": daily_rate,
                "most_common_errors": dict(most_common),
                "error_types": dict(self.error_counts),
                "timestamp": now
            }


# Global error tracker instance
error_tracker = ErrorTracker()


def track_errors(operation: str):
    """Decorator to track errors in functions.
    Preserves function signature for FastAPI and supports async/sync callables.
    """
    import inspect
    import functools

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_tracker.track_error(
                    error_type=f"{operation}_error",
                    error_message=str(e),
                    context={
                        "function": func.__name__,
                        "operation": operation,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    },
                    stack_trace=str(e.__traceback__) if e.__traceback__ else None
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_tracker.track_error(
                    error_type=f"{operation}_error",
                    error_message=str(e),
                    context={
                        "function": func.__name__,
                        "operation": operation,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    },
                    stack_trace=str(e.__traceback__) if e.__traceback__ else None
                )
                raise

        # Choose appropriate wrapper and preserve signature for FastAPI docs
        if inspect.iscoroutinefunction(func):
            try:
                async_wrapper.__signature__ = inspect.signature(func)  # type: ignore[attr-defined]
            except Exception:
                pass
            return async_wrapper
        else:
            try:
                sync_wrapper.__signature__ = inspect.signature(func)  # type: ignore[attr-defined]
            except Exception:
                pass
            return sync_wrapper

    return decorator


def track_api_errors(endpoint: str):
    """Decorator specifically for tracking API endpoint errors."""
    return track_errors(f"api_{endpoint}")


def track_database_errors(operation: str):
    """Decorator specifically for tracking database operation errors."""
    return track_errors(f"db_{operation}")


def track_celery_errors(task_name: str):
    """Decorator specifically for tracking Celery task errors."""
    return track_errors(f"celery_{task_name}")


def track_file_errors(operation: str):
    """Decorator specifically for tracking file operation errors."""
    return track_errors(f"file_{operation}")


class ErrorAlert:
    """Error alert configuration and handling."""
    
    def __init__(self, error_type: str, threshold: int, time_window: float = 3600):
        self.error_type = error_type
        self.threshold = threshold
        self.time_window = time_window
        self.last_alert_time = 0
        self.alert_cooldown = 300  # 5 minutes between alerts
    
    def should_alert(self, current_count: int) -> bool:
        """Check if an alert should be triggered."""
        now = time.time()
        
        # Check if enough time has passed since last alert
        if now - self.last_alert_time < self.alert_cooldown:
            return False
        
        # Check if threshold is exceeded
        if current_count >= self.threshold:
            self.last_alert_time = now
            return True
        
        return False


def create_error_alert(error_type: str, threshold: int, 
                      callback: Optional[Callable] = None) -> ErrorAlert:
    """Create an error alert configuration."""
    alert = ErrorAlert(error_type, threshold)
    
    if callback:
        error_tracker.add_alert_callback(callback)
    
    return alert


def get_error_health_status() -> Dict[str, Any]:
    """Get overall error health status."""
    stats = error_tracker.get_error_stats()
    
    # Determine health status
    total_errors = stats["total_errors"]
    hourly_rate = stats["hourly_rate"]
    daily_rate = stats["daily_rate"]
    
    # Health thresholds (configurable)
    hourly_threshold = 50
    daily_threshold = 1000
    
    if hourly_rate > hourly_threshold or daily_rate > daily_threshold:
        status = "unhealthy"
    elif hourly_rate > hourly_threshold // 2 or daily_rate > daily_threshold // 2:
        status = "warning"
    else:
        status = "healthy"
    
    return {
        "status": status,
        "total_errors": total_errors,
        "hourly_rate": hourly_rate,
        "daily_rate": daily_rate,
        "thresholds": {
            "hourly_warning": hourly_threshold // 2,
            "hourly_critical": hourly_threshold,
            "daily_warning": daily_threshold // 2,
            "daily_critical": daily_threshold
        },
        "timestamp": time.time()
    }


# Export main functions and classes
__all__ = [
    "ErrorTracker",
    "ErrorRecord",
    "ErrorAlert",
    "error_tracker",
    "track_errors",
    "track_api_errors",
    "track_database_errors",
    "track_celery_errors",
    "track_file_errors",
    "create_error_alert",
    "get_error_health_status"
] 