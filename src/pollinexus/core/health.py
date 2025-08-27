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
from .logging import logger
from .database import get_db
from .metrics import ResourceMonitor


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
    
    def register_check(self, name: str, check_function: Callable, 
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
            result = await asyncio.wait_for(
                check.check_function(),
                timeout=check.timeout
            )
            
            duration = time.time() - start_time
            
            health_result = HealthResult(
                name=name,
                status=HealthStatus(result.get("status", "unknown")),
                message=result.get("message", ""),
                details=result.get("details", {}),
                duration=duration
            )
            
            self.last_results[name] = health_result
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
        
        # Run all checks concurrently
        tasks = {
            name: self.run_check(name) 
            for name, check in self.checks.items() 
            if check.enabled
        }
        
        completed_results = await asyncio.gather(
            *tasks.values(), return_exceptions=True
        )
        
        # Process results
        for name, result in zip(tasks.keys(), completed_results):
            if isinstance(result, Exception):
                results[name] = HealthResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message="Health check exception",
                    error=str(result)
                )
            else:
                results[name] = result
        
        # Calculate overall status
        overall_status = self._calculate_overall_status(results)
        total_duration = time.time() - start_time
        
        return {
            "status": overall_status.value,
            "timestamp": time.time(),
            "duration": total_duration,
            "uptime": time.time() - self.startup_time,
            "version": settings.version,
            "environment": settings.environment,
            "checks": {
                name: {
                    "status": result.status.value,
                    "message": result.message,
                    "duration": result.duration,
                    "details": result.details,
                    "error": result.error
                }
                for name, result in results.items()
            }
        }
    
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
            db = next(get_db())
            start_time = time.time()
            
            # Test basic connectivity
            result = db.execute(text("SELECT 1"))
            query_time = time.time() - start_time
            
            # Get database info if possible
            try:
                db_size = db.execute(text("SELECT pg_database_size(current_database())")).scalar()
            except:
                db_size = None  # DuckDB doesn't support this
            
            db.close()
            
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
    return await health_monitor.run_all_checks()


async def get_quick_health() -> Dict[str, Any]:
    """Get quick health status (essential checks only)."""
    essential_checks = ["database", "disk_space", "system_resources"]
    
    results = {}
    for check_name in essential_checks:
        if check_name in health_monitor.checks:
            results[check_name] = await health_monitor.run_check(check_name)
    
    overall_status = health_monitor._calculate_overall_status(results)
    
    return {
        "status": overall_status.value,
        "timestamp": time.time(),
        "checks": {
            name: {
                "status": result.status.value,
                "message": result.message,
                "duration": result.duration
            }
            for name, result in results.items()
        }
    }


def register_health_check(name: str, check_function: Callable, 
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