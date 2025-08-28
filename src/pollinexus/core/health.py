"""
Comprehensive health check system for Pollinexus API.

This module provides detailed health monitoring for all system components
including database, cache, external services, and resource utilization.
"""

import time
import psutil
import asyncio
from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import gc

from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import settings
from .logging import logger, get_monitoring_metrics, log_monitor
from .database import SessionLocal


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Individual health check configuration."""
    name: str
    check_function: Callable[[], Awaitable[Dict[str, Any]]]
    timeout: float = 30.0
    critical: bool = True
    enabled: bool = True


@dataclass
class HealthResult:
    """Health check result."""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0
    timestamp: float = field(default_factory=time.time)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "duration": self.duration,
            "timestamp": self.timestamp,
            "error": self.error
        }


class HealthMonitor:
    """Comprehensive health monitoring system."""
    
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.last_results: Dict[str, HealthResult] = {}
        self.startup_time = time.time()
        
        # Register default checks
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Register default system health checks."""
        self.register_check(
            "database",
            self._check_database,
            timeout=10.0,
            critical=True
        )
        
        self.register_check(
            "system_resources",
            self._check_system_resources,
            timeout=5.0,
            critical=False
        )
        
        self.register_check(
            "disk_space",
            self._check_disk_space,
            timeout=5.0,
            critical=True
        )
        
        self.register_check(
            "logging_system",
            self._check_logging_system,
            timeout=5.0,
            critical=False
        )
        
        self.register_check(
            "memory_usage",
            self._check_memory_usage,
            timeout=5.0,
            critical=False
        )
        
        self.register_check(
            "application_status",
            self._check_application_status,
            timeout=5.0,
            critical=False
        )
    
    def register_check(self, name: str, check_function: Callable[[], Awaitable[Dict[str, Any]]], 
                      timeout: float = 30.0, critical: bool = True, enabled: bool = True):
        """Register a new health check."""
        self.checks[name] = HealthCheck(
            name=name,
            check_function=check_function,
            timeout=timeout,
            critical=critical,
            enabled=enabled
        )
        
        logger.info(f"Registered health check: {name}", extra={
            "health_check": name,
            "timeout": timeout,
            "critical": critical,
            "enabled": enabled
        })
    
    async def run_check(self, name: str) -> HealthResult:
        """Run a specific health check."""
        if name not in self.checks:
            return HealthResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                message="Health check not found",
                error="Check not registered"
            )
        
        check = self.checks[name]
        if not check.enabled:
            return HealthResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                message="Health check disabled"
            )
        
        start_time = time.time()
        
        try:
            # Run check with timeout
            logger.debug(f"Running health check: {name}")
            
            # Ensure the check function is callable
            if not callable(check.check_function):
                raise ValueError(f"Health check function for {name} is not callable")
            
            # Call the check function and await the result
            check_result = check.check_function()
            
            # Ensure we got a coroutine
            if not asyncio.iscoroutine(check_result):
                raise ValueError(f"Health check function for {name} did not return a coroutine")
            
            result = await asyncio.wait_for(
                check_result,
                timeout=check.timeout
            )
            
            duration = time.time() - start_time
            
            # Validate result structure
            if not isinstance(result, dict):
                raise ValueError(f"Health check {name} returned {type(result).__name__}, expected dict")
            
            if "status" not in result:
                raise ValueError(f"Health check {name} missing 'status' field")
            
            # Safely convert status string to HealthStatus enum
            status_str = result.get("status", "unknown")
            try:
                status_enum = HealthStatus(status_str)
            except ValueError:
                status_enum = HealthStatus.UNKNOWN
                logger.warning(f"Invalid health status '{status_str}' for check {name}, using UNKNOWN")
            
            health_result = HealthResult(
                name=name,
                status=status_enum,
                message=result.get("message", ""),
                details=result.get("details", {}),
                duration=duration
            )
            
            self.last_results[name] = health_result
            logger.debug(f"Health check {name} completed successfully")
            return health_result
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            error_msg = f"Health check timed out after {check.timeout}s"
            
            health_result = HealthResult(
                name=name,
                status=HealthStatus.CRITICAL,
                message="Health check timeout",
                duration=duration,
                error=error_msg
            )
            
            self.last_results[name] = health_result
            logger.error(f"Health check {name} timed out", extra={
                "health_check": name,
                "timeout": check.timeout,
                "duration": duration
            })
            
            return health_result
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            
            health_result = HealthResult(
                name=name,
                status=HealthStatus.CRITICAL,
                message="Health check failed",
                duration=duration,
                error=error_msg
            )
            
            self.last_results[name] = health_result
            logger.error(f"Health check {name} failed", extra={
                "health_check": name,
                "error": error_msg,
                "duration": duration
            })
            
            return health_result
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all enabled health checks."""
        start_time = time.time()
        results = {}
        
        logger.debug("Starting health checks", extra={
            "enabled_checks": [name for name, check in self.checks.items() if check.enabled]
        })
        
        # Run all checks concurrently
        tasks = {
            name: self.run_check(name) 
            for name, check in self.checks.items() 
            if check.enabled
        }
        
        try:
            completed_results = await asyncio.gather(
                *tasks.values(), return_exceptions=True
            )
            
            # Process results
            for name, result in zip(tasks.keys(), completed_results):
                if isinstance(result, Exception):
                    logger.error(f"Health check {name} failed with exception", extra={
                        "health_check": name,
                        "error": str(result),
                        "error_type": type(result).__name__
                    })
                    results[name] = HealthResult(
                        name=name,
                        status=HealthStatus.CRITICAL,
                        message="Health check exception",
                        error=str(result)
                    )
                else:
                    results[name] = result
                    
        except Exception as e:
            logger.error("Failed to gather health check results", extra={
                "error": str(e),
                "error_type": type(e).__name__
            })
            # Create error results for all checks
            for name in tasks.keys():
                results[name] = HealthResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message="Health check gathering failed",
                    error=str(e)
                )
        
        # Calculate overall status
        overall_status = self._calculate_overall_status(results)
        total_duration = time.time() - start_time
        
        # Convert all HealthResult objects to plain dictionaries
        checks_dict = {}
        for name, result in results.items():
            try:
                checks_dict[name] = result.to_dict()
            except Exception as e:
                logger.error(f"Failed to convert health result for {name}", extra={
                    "health_check": name,
                    "error": str(e),
                    "result_type": type(result).__name__
                })
                # Create a fallback result
                checks_dict[name] = {
                    "name": name,
                    "status": "critical",
                    "message": "Failed to serialize result",
                    "details": {},
                    "duration": 0.0,
                    "timestamp": time.time(),
                    "error": str(e)
                }
        
        result_dict = {
            "status": overall_status.value,
            "timestamp": time.time(),
            "duration": total_duration,
            "uptime": time.time() - self.startup_time,
            "version": settings.version,
            "environment": settings.environment,
            "checks": checks_dict
        }
        
        logger.debug("Health checks completed", extra={
            "overall_status": overall_status.value,
            "total_duration": total_duration,
            "checks_count": len(checks_dict)
        })
        
        return result_dict
    
    def _calculate_overall_status(self, results: Dict[str, HealthResult]) -> HealthStatus:
        """Calculate overall system health status."""
        critical_failures = []
        warnings = []
        
        for name, result in results.items():
            check = self.checks.get(name)
            if not check:
                continue
            
            if result.status == HealthStatus.CRITICAL:
                if check.critical:
                    critical_failures.append(name)
                else:
                    warnings.append(name)
            elif result.status == HealthStatus.WARNING:
                warnings.append(name)
        
        if critical_failures:
            return HealthStatus.CRITICAL
        elif warnings:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            # Create a session directly instead of using the generator
            db = SessionLocal()
            start_time = time.time()
            
            try:
                # Test basic connectivity
                from sqlalchemy import text
                result = db.execute(text("SELECT 1"))
                query_time = time.time() - start_time
                
                # Get database info if possible
                try:
                    db_size = db.execute(text("SELECT pg_database_size(current_database())")).scalar()
                except:
                    db_size = None  # DuckDB doesn't support this
                
                status = HealthStatus.HEALTHY
                message = "Database connection healthy"
                
                # Check query performance
                if query_time > 1.0:
                    status = HealthStatus.WARNING
                    message = "Database query slow"
                elif query_time > 5.0:
                    status = HealthStatus.CRITICAL
                    message = "Database query very slow"
                
                return {
                    "status": status.value,
                    "message": message,
                    "details": {
                        "query_time": query_time,
                        "database_size": db_size,
                        "connection_pool_size": settings.database_pool_size
                    }
                }
                
            finally:
                db.close()
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL.value,
                "message": "Database connection failed",
                "details": {"error": str(e)}
            }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource utilization."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Determine status based on usage
            status = HealthStatus.HEALTHY
            warnings = []
            
            if cpu_percent > 90:
                status = HealthStatus.CRITICAL
                warnings.append("CPU usage critical")
            elif cpu_percent > 80:
                status = HealthStatus.WARNING
                warnings.append("CPU usage high")
            
            if memory.percent > 95:
                status = HealthStatus.CRITICAL
                warnings.append("Memory usage critical")
            elif memory.percent > 85:
                status = HealthStatus.WARNING
                warnings.append("Memory usage high")
            
            message = "System resources healthy"
            if warnings:
                message = "; ".join(warnings)
            
            return {
                "status": status.value,
                "message": message,
                "details": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / 1024 / 1024 / 1024,
                    "memory_total_gb": memory.total / 1024 / 1024 / 1024
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL.value,
                "message": "Failed to check system resources",
                "details": {"error": str(e)}
            }
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space."""
        try:
            disk = psutil.disk_usage('/')
            free_percent = (disk.free / disk.total) * 100
            
            status = HealthStatus.HEALTHY
            message = "Disk space healthy"
            
            if free_percent < 5:
                status = HealthStatus.CRITICAL
                message = "Disk space critical"
            elif free_percent < 10:
                status = HealthStatus.WARNING
                message = "Disk space low"
            
            return {
                "status": status.value,
                "message": message,
                "details": {
                    "free_percent": free_percent,
                    "free_gb": disk.free / 1024 / 1024 / 1024,
                    "total_gb": disk.total / 1024 / 1024 / 1024,
                    "used_gb": disk.used / 1024 / 1024 / 1024
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL.value,
                "message": "Failed to check disk space",
                "details": {"error": str(e)}
            }
    
    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check application memory usage and garbage collection."""
        try:
            # Process memory info
            process = psutil.Process()
            process_memory = process.memory_info()
            
            # Garbage collection stats
            gc_stats = {
                f"generation_{i}": count 
                for i, count in enumerate(gc.get_count())
            }
            
            # Calculate memory usage in MB
            rss_mb = process_memory.rss / 1024 / 1024
            vms_mb = process_memory.vms / 1024 / 1024
            
            status = HealthStatus.HEALTHY
            message = "Memory usage normal"
            
            # Check for memory issues
            if rss_mb > settings.max_memory_usage_mb:
                status = HealthStatus.CRITICAL
                message = "Memory usage exceeds limit"
            elif rss_mb > settings.max_memory_usage_mb * 0.8:
                status = HealthStatus.WARNING
                message = "Memory usage high"
            
            return {
                "status": status.value,
                "message": message,
                "details": {
                    "rss_mb": rss_mb,
                    "vms_mb": vms_mb,
                    "max_memory_mb": settings.max_memory_usage_mb,
                    "memory_percent": (rss_mb / settings.max_memory_usage_mb) * 100,
                    "gc_stats": gc_stats,
                    "open_files": len(process.open_files()),
                    "threads": process.num_threads()
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL.value,
                "message": "Failed to check memory usage",
                "details": {"error": str(e)}
            }
    
    async def _check_application_status(self) -> Dict[str, Any]:
        """Check application-specific health indicators."""
        try:
            # Check configuration
            config_warnings = settings.validate_configuration()
            
            # Check file system permissions
            upload_path = settings.get_upload_path()
            can_write = upload_path.exists() and upload_path.is_dir()
            
            status = HealthStatus.HEALTHY
            warnings = []
            
            if config_warnings:
                warnings.extend(config_warnings)
                if any("production" in w.lower() for w in config_warnings):
                    status = HealthStatus.WARNING
            
            if not can_write:
                status = HealthStatus.CRITICAL
                warnings.append("Cannot write to upload directory")
            
            message = "Application healthy"
            if warnings:
                message = f"Application issues: {len(warnings)} warnings"
            
            return {
                "status": status.value,
                "message": message,
                "details": {
                    "config_warnings": config_warnings,
                    "upload_directory_writable": can_write,
                    "upload_directory": str(upload_path),
                    "environment": settings.environment,
                    "debug_mode": settings.debug
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL.value,
                "message": "Failed to check application status",
                "details": {"error": str(e)}
            }
    
    async def _check_logging_system(self) -> Dict[str, Any]:
        """Check logging system health and metrics."""
        try:
            # Get monitoring metrics
            metrics = get_monitoring_metrics()
            
            # Calculate error rate
            total_errors = sum(metrics['error_counts'].values())
            total_warnings = sum(metrics['warning_counts'].values())
            
            # Check for critical issues
            critical_errors = metrics['error_counts'].get('critical', 0)
            high_error_rate = any(
                count > 10 for count in metrics['error_counts'].values()
            )
            
            # Check performance issues
            slow_operations = [
                op for op, data in metrics['performance_metrics'].items()
                if data.get('avg_time', 0) > 5.0
            ]
            
            # Determine status
            if critical_errors > 0:
                status = HealthStatus.CRITICAL
                message = f"Critical errors detected: {critical_errors}"
            elif high_error_rate:
                status = HealthStatus.WARNING
                message = "High error rate detected"
            elif slow_operations:
                status = HealthStatus.WARNING
                message = f"Slow operations detected: {len(slow_operations)}"
            else:
                status = HealthStatus.HEALTHY
                message = "Logging system healthy"
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "total_errors": total_errors,
                    "total_warnings": total_warnings,
                    "critical_errors": critical_errors,
                    "slow_operations": slow_operations,
                    "error_counts": metrics['error_counts'],
                    "performance_metrics": {
                        op: {
                            'count': data.get('count', 0),
                            'avg_time': data.get('avg_time', 0),
                            'max_time': data.get('max_time', 0)
                        }
                        for op, data in metrics['performance_metrics'].items()
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Logging system health check failed: {e}")
            return {
                "status": HealthStatus.CRITICAL,
                "message": f"Logging system health check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of the last health check results."""
        if not self.last_results:
            return {
                "status": "unknown",
                "message": "No health checks have been run",
                "last_check": None
            }
        
        # Calculate overall status from last results
        overall_status = self._calculate_overall_status(self.last_results)
        
        # Find most recent check
        latest_check = max(
            self.last_results.values(),
            key=lambda r: r.timestamp
        )
        
        return {
            "status": overall_status.value,
            "message": f"Last health check: {datetime.fromtimestamp(latest_check.timestamp)}",
            "last_check": latest_check.timestamp,
            "uptime": time.time() - self.startup_time,
            "checks_count": len(self.last_results),
            "failed_checks": [
                name for name, result in self.last_results.items()
                if result.status == HealthStatus.CRITICAL
            ]
        }


# Global health monitor instance
health_monitor = HealthMonitor()


# Convenience functions for common health checks
async def get_health_status() -> Dict[str, Any]:
    """Get comprehensive health status."""
    try:
        result = await health_monitor.run_all_checks()
        
        # Ensure the result is JSON serializable
        if not isinstance(result, dict):
            raise ValueError(f"Health monitor returned {type(result).__name__}, expected dict")
        
        logger.debug("Health status check completed", extra={
            "result_type": type(result).__name__,
            "result_keys": list(result.keys()) if isinstance(result, dict) else "not_dict"
        })
        
        # Validate the result structure
        required_keys = ["status", "timestamp", "checks"]
        missing_keys = [key for key in required_keys if key not in result]
        if missing_keys:
            raise ValueError(f"Health status result missing required keys: {missing_keys}")
        
        return result
        
    except Exception as e:
        logger.error("Health status check failed", extra={
            "error": str(e),
            "error_type": type(e).__name__
        })
        
        # Return a fallback response instead of raising
        return {
            "status": "critical",
            "timestamp": time.time(),
            "duration": 0.0,
            "uptime": time.time() - health_monitor.startup_time,
            "version": getattr(settings, 'version', 'unknown'),
            "environment": getattr(settings, 'environment', 'unknown'),
            "checks": {
                "error": {
                    "name": "error",
                    "status": "critical",
                    "message": "Health check system error",
                    "details": {},
                    "duration": 0.0,
                    "timestamp": time.time(),
                    "error": str(e)
                }
            }
        }


async def get_quick_health() -> Dict[str, Any]:
    """Get quick health status (essential checks only)."""
    essential_checks = ["database", "disk_space", "system_resources"]
    
    results = {}
    for check_name in essential_checks:
        if check_name in health_monitor.checks:
            result = await health_monitor.run_check(check_name)
            # Convert HealthResult to plain dictionary
            results[check_name] = result.to_dict()
    
    # Calculate overall status from the converted results
    critical_failures = []
    warnings = []
    
    for name, result in results.items():
        check = health_monitor.checks.get(name)
        if not check:
            continue
        
        if result["status"] == "critical":
            if check.critical:
                critical_failures.append(name)
            else:
                warnings.append(name)
        elif result["status"] == "warning":
            warnings.append(name)
    
    if critical_failures:
        overall_status = "critical"
    elif warnings:
        overall_status = "warning"
    else:
        overall_status = "healthy"
    
    return {
        "status": overall_status,
        "timestamp": time.time(),
        "checks": results
    }


def register_health_check(name: str, check_function: Callable[[], Awaitable[Dict[str, Any]]], 
                         timeout: float = 30.0, critical: bool = True):
    """Register a custom health check."""
    health_monitor.register_check(name, check_function, timeout, critical)


# Export main components
__all__ = [
    "HealthStatus",
    "HealthCheck", 
    "HealthResult",
    "HealthMonitor",
    "health_monitor",
    "get_health_status",
    "get_quick_health",
    "register_health_check"
] 