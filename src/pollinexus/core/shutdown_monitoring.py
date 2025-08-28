"""
Shutdown monitoring and metrics for Pollinexus.

This module provides comprehensive monitoring, metrics collection,
and alerting for the graceful shutdown process.
"""

import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import json

from .logging import logger
from .config import settings


class ShutdownPhase(Enum):
    """Enumeration of shutdown phases for monitoring."""
    SIGNAL_RECEIVED = "signal_received"
    SYNC_CLEANUP_START = "sync_cleanup_start"
    SYNC_CLEANUP_COMPLETE = "sync_cleanup_complete"
    ASYNC_CLEANUP_START = "async_cleanup_start"
    ASYNC_CLEANUP_COMPLETE = "async_cleanup_complete"
    SHUTDOWN_COMPLETE = "shutdown_complete"
    FORCE_SHUTDOWN = "force_shutdown"


@dataclass
class ShutdownMetrics:
    """Metrics collected during shutdown process."""
    start_time: float
    end_time: Optional[float] = None
    total_duration: Optional[float] = None
    phase_durations: Dict[str, float] = field(default_factory=dict)
    cleanup_tasks: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    resource_cleanup: Dict[str, bool] = field(default_factory=dict)
    signal_info: Dict[str, Any] = field(default_factory=dict)


class ShutdownMonitor:
    """
    Monitors and tracks shutdown process metrics.
    
    Provides comprehensive monitoring, alerting, and reporting
    for the graceful shutdown process.
    """
    
    def __init__(self):
        self._metrics_history: deque = deque(maxlen=100)  # Keep last 100 shutdowns
        self._current_metrics: Optional[ShutdownMetrics] = None
        self._phase_start_times: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._alert_callbacks: List[callable] = []
        
        logger.info(
            "Shutdown monitor initialized",
            extra={
                "component": "shutdown_monitor",
                "operation": "initialization",
                "max_history": 100
            }
        )
    
    def start_shutdown_tracking(self, signal_info: Dict[str, Any]) -> str:
        """
        Start tracking a new shutdown process.
        
        Args:
            signal_info: Information about the shutdown signal
            
        Returns:
            Tracking ID for this shutdown
        """
        with self._lock:
            tracking_id = f"shutdown_{int(time.time() * 1000)}"
            
            self._current_metrics = ShutdownMetrics(
                start_time=time.time(),
                signal_info=signal_info
            )
            
            self._phase_start_times.clear()
            self._phase_start_times[ShutdownPhase.SIGNAL_RECEIVED.value] = time.time()
            
            logger.warning(
                "Shutdown tracking started",
                extra={
                    "component": "shutdown_monitor",
                    "operation": "tracking_start",
                    "tracking_id": tracking_id,
                    "signal_info": signal_info
                }
            )
            
            return tracking_id
    
    def record_phase_start(self, phase: ShutdownPhase):
        """Record the start of a shutdown phase."""
        with self._lock:
            if self._current_metrics:
                self._phase_start_times[phase.value] = time.time()
                
                logger.info(
                    f"Shutdown phase started: {phase.value}",
                    extra={
                        "component": "shutdown_monitor",
                        "operation": "phase_start",
                        "phase": phase.value,
                        "timestamp": time.time()
                    }
                )
    
    def record_phase_complete(self, phase: ShutdownPhase, duration: Optional[float] = None):
        """Record the completion of a shutdown phase."""
        with self._lock:
            if self._current_metrics and phase.value in self._phase_start_times:
                phase_duration = duration or (time.time() - self._phase_start_times[phase.value])
                self._current_metrics.phase_durations[phase.value] = phase_duration
                
                logger.info(
                    f"Shutdown phase completed: {phase.value}",
                    extra={
                        "component": "shutdown_monitor",
                        "operation": "phase_complete",
                        "phase": phase.value,
                        "duration": phase_duration,
                        "timestamp": time.time()
                    }
                )
    
    def record_cleanup_task(self, task_name: str, duration: float, success: bool = True):
        """Record a cleanup task execution."""
        with self._lock:
            if self._current_metrics:
                task_info = f"{task_name}: {duration:.3f}s"
                if not success:
                    task_info += " (FAILED)"
                
                self._current_metrics.cleanup_tasks.append(task_info)
                
                logger.debug(
                    "Cleanup task recorded",
                    extra={
                        "component": "shutdown_monitor",
                        "operation": "cleanup_task",
                        "task_name": task_name,
                        "duration": duration,
                        "success": success
                    }
                )
    
    def record_error(self, error: str, context: Optional[Dict[str, Any]] = None):
        """Record an error during shutdown."""
        with self._lock:
            if self._current_metrics:
                error_info = error
                if context:
                    error_info += f" (context: {json.dumps(context)})"
                
                self._current_metrics.errors.append(error_info)
                
                logger.error(
                    "Shutdown error recorded",
                    extra={
                        "component": "shutdown_monitor",
                        "operation": "error_recorded",
                        "error": error,
                        "context": context
                    }
                )
    
    def record_warning(self, warning: str, context: Optional[Dict[str, Any]] = None):
        """Record a warning during shutdown."""
        with self._lock:
            if self._current_metrics:
                warning_info = warning
                if context:
                    warning_info += f" (context: {json.dumps(context)})"
                
                self._current_metrics.warnings.append(warning_info)
                
                logger.warning(
                    "Shutdown warning recorded",
                    extra={
                        "component": "shutdown_monitor",
                        "operation": "warning_recorded",
                        "warning": warning,
                        "context": context
                    }
                )
    
    def record_resource_cleanup(self, resource: str, success: bool):
        """Record resource cleanup status."""
        with self._lock:
            if self._current_metrics:
                self._current_metrics.resource_cleanup[resource] = success
                
                logger.info(
                    "Resource cleanup recorded",
                    extra={
                        "component": "shutdown_monitor",
                        "operation": "resource_cleanup",
                        "resource": resource,
                        "success": success
                    }
                )
    
    def complete_shutdown_tracking(self) -> ShutdownMetrics:
        """
        Complete shutdown tracking and return metrics.
        
        Returns:
            ShutdownMetrics object with complete shutdown information
        """
        with self._lock:
            if not self._current_metrics:
                raise RuntimeError("No shutdown tracking in progress")
            
            self._current_metrics.end_time = time.time()
            self._current_metrics.total_duration = (
                self._current_metrics.end_time - self._current_metrics.start_time
            )
            
            # Add to history
            self._metrics_history.append(self._current_metrics)
            
            # Generate alerts if needed
            self._check_alerts(self._current_metrics)
            
            # Log completion
            logger.warning(
                "Shutdown tracking completed",
                extra={
                    "component": "shutdown_monitor",
                    "operation": "tracking_complete",
                    "total_duration": self._current_metrics.total_duration,
                    "cleanup_tasks": len(self._current_metrics.cleanup_tasks),
                    "errors": len(self._current_metrics.errors),
                    "warnings": len(self._current_metrics.warnings)
                }
            )
            
            completed_metrics = self._current_metrics
            self._current_metrics = None
            self._phase_start_times.clear()
            
            return completed_metrics
    
    def _check_alerts(self, metrics: ShutdownMetrics):
        """Check if alerts should be generated based on metrics."""
        alerts = []
        
        # Check for long shutdown duration
        if metrics.total_duration and metrics.total_duration > settings.shutdown_graceful_timeout:
            alerts.append({
                "type": "shutdown_duration_exceeded",
                "message": f"Shutdown took {metrics.total_duration:.2f}s (exceeded {settings.shutdown_graceful_timeout}s)",
                "severity": "warning"
            })
        
        # Check for errors
        if metrics.errors:
            alerts.append({
                "type": "shutdown_errors",
                "message": f"Shutdown completed with {len(metrics.errors)} errors",
                "severity": "error",
                "errors": metrics.errors
            })
        
        # Check for failed resource cleanup
        failed_resources = [
            resource for resource, success in metrics.resource_cleanup.items()
            if not success
        ]
        if failed_resources:
            alerts.append({
                "type": "resource_cleanup_failed",
                "message": f"Failed to cleanup resources: {', '.join(failed_resources)}",
                "severity": "error"
            })
        
        # Trigger alert callbacks
        for alert in alerts:
            for callback in self._alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Alert callback failed: {e}")
    
    def register_alert_callback(self, callback: callable):
        """Register a callback for shutdown alerts."""
        self._alert_callbacks.append(callback)
        
        logger.debug(
            "Alert callback registered",
            extra={
                "component": "shutdown_monitor",
                "operation": "register_alert_callback",
                "callback_name": callback.__name__
            }
        )
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current shutdown monitoring status."""
        with self._lock:
            status = {
                "is_tracking": self._current_metrics is not None,
                "current_phase": None,
                "elapsed_time": None,
                "metrics_history_count": len(self._metrics_history)
            }
            
            if self._current_metrics:
                status.update({
                    "elapsed_time": time.time() - self._current_metrics.start_time,
                    "current_phase": self._get_current_phase(),
                    "cleanup_tasks_count": len(self._current_metrics.cleanup_tasks),
                    "errors_count": len(self._current_metrics.errors),
                    "warnings_count": len(self._current_metrics.warnings)
                })
            
            return status
    
    def _get_current_phase(self) -> Optional[str]:
        """Get the current shutdown phase based on recorded phases."""
        if not self._phase_start_times:
            return None
        
        # Determine current phase based on what's been recorded
        phases = list(ShutdownPhase)
        for phase in reversed(phases):
            if phase.value in self._phase_start_times:
                return phase.value
        
        return None
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary statistics of shutdown metrics."""
        with self._lock:
            if not self._metrics_history:
                return {"message": "No shutdown metrics available"}
            
            durations = [m.total_duration for m in self._metrics_history if m.total_duration]
            error_counts = [len(m.errors) for m in self._metrics_history]
            warning_counts = [len(m.warnings) for m in self._metrics_history]
            
            summary = {
                "total_shutdowns": len(self._metrics_history),
                "average_duration": sum(durations) / len(durations) if durations else 0,
                "min_duration": min(durations) if durations else 0,
                "max_duration": max(durations) if durations else 0,
                "average_errors": sum(error_counts) / len(error_counts) if error_counts else 0,
                "average_warnings": sum(warning_counts) / len(warning_counts) if warning_counts else 0,
                "successful_cleanups": sum(1 for m in self._metrics_history if not m.errors),
                "failed_cleanups": sum(1 for m in self._metrics_history if m.errors)
            }
            
            return summary
    
    def get_recent_metrics(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent shutdown metrics."""
        with self._lock:
            recent = list(self._metrics_history)[-count:]
            
            return [{
                "start_time": m.start_time,
                "end_time": m.end_time,
                "total_duration": m.total_duration,
                "cleanup_tasks_count": len(m.cleanup_tasks),
                "errors_count": len(m.errors),
                "warnings_count": len(m.warnings),
                "signal_info": m.signal_info
            } for m in recent]
    
    def clear_history(self):
        """Clear metrics history."""
        with self._lock:
            self._metrics_history.clear()
            
            logger.info(
                "Shutdown metrics history cleared",
                extra={
                    "component": "shutdown_monitor",
                    "operation": "clear_history"
                }
            )


# Global shutdown monitor instance
shutdown_monitor = ShutdownMonitor()


def log_shutdown_alert(alert: Dict[str, Any]):
    """Default alert callback that logs shutdown alerts."""
    log_level = alert.get("severity", "warning").upper()
    message = alert.get("message", "Unknown alert")
    
    log_data = {
        "component": "shutdown_monitor",
        "operation": "alert",
        "alert_type": alert.get("type"),
        "severity": alert.get("severity"),
        "message": message
    }
    
    if log_level == "ERROR":
        logger.error(f"Shutdown Alert: {message}", extra=log_data)
    elif log_level == "WARNING":
        logger.warning(f"Shutdown Alert: {message}", extra=log_data)
    else:
        logger.info(f"Shutdown Alert: {message}", extra=log_data)


# Register default alert callback
shutdown_monitor.register_alert_callback(log_shutdown_alert) 