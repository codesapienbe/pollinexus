"""
Performance monitoring and metrics collection for Pollinexus API.

This module provides decorators and utilities for monitoring
performance, resource usage, and application metrics.
"""

import time
import functools
import psutil
import threading
from typing import Any, Callable, Dict, Optional, Union
from contextlib import contextmanager
from collections import defaultdict, deque
import statistics

from .logging import logger, request_id, correlation_id


class PerformanceMetrics:
    """Performance metrics collector and analyzer."""
    
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self.metrics = defaultdict(lambda: deque(maxlen=max_samples))
        self.lock = threading.Lock()
    
    def record_metric(self, operation: str, value: float, **context):
        """Record a performance metric."""
        with self.lock:
            metric_data = {
                "value": value,
                "timestamp": time.time(),
                **context
            }
            self.metrics[operation].append(metric_data)
    
    def get_metrics(self, operation: str) -> Dict[str, Any]:
        """Get aggregated metrics for an operation."""
        with self.lock:
            if operation not in self.metrics or not self.metrics[operation]:
                return {}
            
            values = [m["value"] for m in self.metrics[operation]]
            
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                "p95": self._percentile(values, 95),
                "p99": self._percentile(values, 99),
                "latest": values[-1] if values else 0
            }
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all operations."""
        with self.lock:
            return {op: self.get_metrics(op) for op in self.metrics.keys()}
    
    def _percentile(self, values: list, percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def clear_metrics(self, operation: Optional[str] = None):
        """Clear metrics for an operation or all operations."""
        with self.lock:
            if operation:
                if operation in self.metrics:
                    self.metrics[operation].clear()
            else:
                self.metrics.clear()


# Global metrics instance
performance_metrics = PerformanceMetrics()


def monitor_performance(operation: str):
    """Decorator to monitor function performance."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            req_id = request_id.get()
            corr_id = correlation_id.get()
            
            # Get initial resource usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            initial_cpu = process.cpu_percent()
            
            try:
                # Execute async function
                result = await func(*args, **kwargs)
                
                # Calculate metrics
                execution_time = time.time() - start_time
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                final_cpu = process.cpu_percent()
                
                # Record metrics
                performance_metrics.record_metric(
                    operation,
                    execution_time,
                    request_id=req_id,
                    correlation_id=corr_id,
                    memory_delta=final_memory - initial_memory,
                    cpu_usage=final_cpu
                )
                
                # Log performance
                logger.info(
                    f"Performance: {operation} completed",
                    extra={
                        "operation": operation,
                        "execution_time": execution_time,
                        "memory_delta": final_memory - initial_memory,
                        "cpu_usage": final_cpu,
                        "request_id": req_id,
                        "correlation_id": corr_id
                    }
                )
                
                return result
                
            except Exception as e:
                # Calculate metrics even for failed operations
                execution_time = time.time() - start_time
                
                # Record metrics
                performance_metrics.record_metric(
                    f"{operation}_error",
                    execution_time,
                    request_id=req_id,
                    correlation_id=corr_id,
                    error=str(e)
                )
                
                # Log error performance
                logger.error(
                    f"Performance: {operation} failed",
                    extra={
                        "operation": operation,
                        "execution_time": execution_time,
                        "error": str(e),
                        "request_id": req_id,
                        "correlation_id": corr_id
                    }
                )
                
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            req_id = request_id.get()
            corr_id = correlation_id.get()
            
            # Get initial resource usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            initial_cpu = process.cpu_percent()
            
            try:
                # Execute sync function
                result = func(*args, **kwargs)
                
                # Calculate metrics
                execution_time = time.time() - start_time
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                final_cpu = process.cpu_percent()
                
                # Record metrics
                performance_metrics.record_metric(
                    operation,
                    execution_time,
                    request_id=req_id,
                    correlation_id=corr_id,
                    memory_delta=final_memory - initial_memory,
                    cpu_usage=final_cpu
                )
                
                # Log performance
                logger.info(
                    f"Performance: {operation} completed",
                    extra={
                        "operation": operation,
                        "execution_time": execution_time,
                        "memory_delta": final_memory - initial_memory,
                        "cpu_usage": final_cpu,
                        "request_id": req_id,
                        "correlation_id": corr_id
                    }
                )
                
                return result
                
            except Exception as e:
                # Calculate metrics even for failed operations
                execution_time = time.time() - start_time
                
                # Record metrics
                performance_metrics.record_metric(
                    f"{operation}_error",
                    execution_time,
                    request_id=req_id,
                    correlation_id=corr_id,
                    error=str(e)
                )
                
                # Log error performance
                logger.error(
                    f"Performance: {operation} failed",
                    extra={
                        "operation": operation,
                        "execution_time": execution_time,
                        "error": str(e),
                        "request_id": req_id,
                        "correlation_id": corr_id
                    }
                )
                
                raise
        
        # Return the appropriate wrapper based on whether the function is async
        import inspect
        if inspect.iscoroutinefunction(func):
            # Preserve original function signature for FastAPI docs
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


@contextmanager
def performance_monitor(operation: str, **context):
    """Context manager for monitoring performance of code blocks."""
    start_time = time.time()
    req_id = request_id.get()
    corr_id = correlation_id.get()
    
    # Get initial resource usage
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    initial_cpu = process.cpu_percent()
    
    try:
        yield
        
        # Calculate metrics
        execution_time = time.time() - start_time
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = process.cpu_percent()
        
        # Record metrics
        performance_metrics.record_metric(
            operation,
            execution_time,
            request_id=req_id,
            correlation_id=corr_id,
            memory_delta=final_memory - initial_memory,
            cpu_usage=final_cpu,
            **context
        )
        
        # Log performance
        logger.info(
            f"Performance: {operation} completed",
            extra={
                "operation": operation,
                "execution_time": execution_time,
                "memory_delta": final_memory - initial_memory,
                "cpu_usage": final_cpu,
                "request_id": req_id,
                "correlation_id": corr_id,
                **context
            }
        )
        
    except Exception as e:
        # Calculate metrics even for failed operations
        execution_time = time.time() - start_time
        
        # Record metrics
        performance_metrics.record_metric(
            f"{operation}_error",
            execution_time,
            request_id=req_id,
            correlation_id=corr_id,
            error=str(e),
            **context
        )
        
        # Log error performance
        logger.error(
            f"Performance: {operation} failed",
            extra={
                "operation": operation,
                "execution_time": execution_time,
                "error": str(e),
                "request_id": req_id,
                "correlation_id": corr_id,
                **context
            }
        )
        
        raise


class ResourceMonitor:
    """Monitor system resource usage."""
    
    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Get current system resource metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_metrics = {
                "total_gb": memory.total / 1024 / 1024 / 1024,
                "available_gb": memory.available / 1024 / 1024 / 1024,
                "used_gb": memory.used / 1024 / 1024 / 1024,
                "percent": memory.percent
            }
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_metrics = {
                "total_gb": disk.total / 1024 / 1024 / 1024,
                "used_gb": disk.used / 1024 / 1024 / 1024,
                "free_gb": disk.free / 1024 / 1024 / 1024,
                "percent": (disk.used / disk.total) * 100
            }
            
            # Process metrics
            process = psutil.Process()
            process_metrics = {
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_percent": process.cpu_percent(),
                "threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections())
            }
            
            return {
                "timestamp": time.time(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": memory_metrics,
                "disk": disk_metrics,
                "process": process_metrics
            }
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def get_process_metrics() -> Dict[str, Any]:
        """Get current process resource metrics."""
        try:
            process = psutil.Process()
            
            return {
                "timestamp": time.time(),
                "pid": process.pid,
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_percent": process.cpu_percent(),
                "threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections()),
                "status": process.status()
            }
            
        except Exception as e:
            logger.error(f"Failed to get process metrics: {e}")
            return {"error": str(e)}


def get_performance_summary() -> Dict[str, Any]:
    """Get a summary of all performance metrics."""
    try:
        # Get all metrics
        all_metrics = performance_metrics.get_all_metrics()
        
        # Get system metrics
        system_metrics = ResourceMonitor.get_system_metrics()
        
        # Calculate overall statistics
        all_execution_times = []
        for operation_metrics in all_metrics.values():
            if operation_metrics:
                all_execution_times.extend([m["value"] for m in performance_metrics.metrics[operation_metrics.get("operation", "unknown")]])
        
        overall_stats = {}
        if all_execution_times:
            overall_stats = {
                "total_operations": len(all_execution_times),
                "avg_execution_time": statistics.mean(all_execution_times),
                "max_execution_time": max(all_execution_times),
                "min_execution_time": min(all_execution_times)
            }
        
        return {
            "timestamp": time.time(),
            "operations": all_metrics,
            "overall_stats": overall_stats,
            "system": system_metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        return {"error": str(e)}


def reset_performance_metrics():
    """Reset all performance metrics."""
    performance_metrics.clear_metrics()
    logger.info("Performance metrics reset")


# Utility functions for common monitoring patterns
def monitor_api_endpoint(endpoint: str):
    """Decorator specifically for monitoring API endpoints."""
    return monitor_performance(f"api_{endpoint}")


def monitor_database_operation(operation: str):
    """Decorator specifically for monitoring database operations."""
    return monitor_performance(f"db_{operation}")


def monitor_celery_task(task_name: str):
    """Decorator specifically for monitoring Celery tasks."""
    return monitor_performance(f"celery_{task_name}")


def monitor_file_operation(operation: str):
    """Decorator specifically for monitoring file operations."""
    return monitor_performance(f"file_{operation}")


# Export main decorator for convenience
__all__ = [
    "monitor_performance",
    "performance_monitor",
    "PerformanceMetrics",
    "ResourceMonitor",
    "get_performance_summary",
    "reset_performance_metrics",
    "monitor_api_endpoint",
    "monitor_database_operation",
    "monitor_celery_task",
    "monitor_file_operation"
] 