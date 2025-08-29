"""
Graceful shutdown management for Pollinexus.

This module provides comprehensive shutdown handling with signal management,
resource cleanup, and structured logging for monitoring.
"""

import signal
import asyncio
import threading
import time
import sys
from typing import List, Callable, Dict, Any, Optional
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum

from .logging import logger
from .config import settings
from .shutdown_monitoring import shutdown_monitor, ShutdownPhase


class ShutdownReason(Enum):
    """Enumeration of shutdown reasons for monitoring."""
    SIGNAL_INTERRUPT = "signal_interrupt"
    SIGNAL_TERMINATE = "signal_terminate"
    MANUAL_SHUTDOWN = "manual_shutdown"
    HEALTH_CHECK_FAILURE = "health_check_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    UNKNOWN = "unknown"


@dataclass
class ShutdownContext:
    """Context information for shutdown operations."""
    reason: ShutdownReason
    signal_number: Optional[int] = None
    graceful_timeout: int = 30
    force_timeout: int = 5
    start_time: float = field(default_factory=time.time)
    cleanup_tasks: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class GracefulShutdownManager:
    """
    Manages graceful shutdown of the Pollinexus application.
    
    Handles signal interception, resource cleanup, and monitoring
    with comprehensive logging for enterprise environments.
    """
    
    def __init__(self):
        self._shutdown_event = threading.Event()
        self._cleanup_handlers: List[Callable] = []
        self._async_cleanup_handlers: List[Callable] = []
        self._shutdown_context: Optional[ShutdownContext] = None
        self._original_signal_handlers: Dict[int, Any] = {}
        self._is_shutting_down = False
        self._shutdown_lock = threading.Lock()
        
        # Double CTRL+C tracking
        self._sigint_count = 0
        self._sigint_last_time = 0
        self._sigint_window = 2.0  # 2 second window for double CTRL+C
        
        # Register default signal handlers (enable in development for double CTRL+C)
        if getattr(settings, "shutdown_enable_signal_handling", True):
            self._register_signal_handlers()
        
        logger.info(
            "Graceful shutdown manager initialized",
            extra={
                "component": "shutdown_manager",
                "operation": "initialization",
                "graceful_timeout": 30,
                "force_timeout": 5,
                "double_ctrlc_window": self._sigint_window
            }
        )
    
    def _register_signal_handlers(self):
        """Register signal handlers for graceful shutdown."""
        try:
            # SIGINT (Ctrl+C)
            self._original_signal_handlers[signal.SIGINT] = signal.signal(
                signal.SIGINT, self._signal_handler
            )
            
            # SIGTERM (termination request)
            self._original_signal_handlers[signal.SIGTERM] = signal.signal(
                signal.SIGTERM, self._signal_handler
            )
            
            # SIGUSR1 (custom graceful shutdown) - only on Unix systems
            try:
                if hasattr(signal, 'SIGUSR1'):
                    self._original_signal_handlers[signal.SIGUSR1] = signal.signal(
                        signal.SIGUSR1, self._signal_handler
                    )
            except (AttributeError, OSError):
                # SIGUSR1 not available on Windows
                pass
            
            logger.info(
                "Signal handlers registered",
                extra={
                    "component": "shutdown_manager",
                    "operation": "signal_registration",
                    "signals": ["SIGINT", "SIGTERM", "SIGUSR1"]
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to register signal handlers",
                extra={
                    "component": "shutdown_manager",
                    "operation": "signal_registration",
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
    
    def _signal_handler(self, signum: int, frame):
        """Handle shutdown signals with comprehensive logging and double CTRL+C support."""
        
        current_time = time.time()
        
        # Special handling for SIGINT (CTRL+C)
        if signum == signal.SIGINT:
            # Check if this is within the double-press window
            if (current_time - self._sigint_last_time) <= self._sigint_window:
                self._sigint_count += 1
                logger.warning(
                    f"CTRL+C pressed {self._sigint_count} times",
                    extra={
                        "component": "shutdown_manager",
                        "operation": "signal_handler",
                        "signal_number": signum,
                        "signal_name": "SIGINT",
                        "sigint_count": self._sigint_count,
                        "time_since_last": current_time - self._sigint_last_time
                    }
                )
                
                # Second CTRL+C triggers cold shutdown
                if self._sigint_count >= 2:
                    logger.critical(
                        "Double CTRL+C detected - initiating cold shutdown",
                        extra={
                            "component": "shutdown_manager",
                            "operation": "cold_shutdown",
                            "signal_number": signum,
                            "signal_name": "SIGINT",
                            "sigint_count": self._sigint_count
                        }
                    )
                    
                    # Force immediate shutdown
                    self._force_cold_shutdown()
                    return
                else:
                    # First CTRL+C - show warning and continue
                    print(f"\n⚠️  Press CTRL+C again within {self._sigint_window} seconds to force shutdown")
                    self._sigint_last_time = current_time
                    return
            else:
                # Reset counter if outside window
                self._sigint_count = 1
                self._sigint_last_time = current_time
                logger.warning(
                    "CTRL+C pressed (first time)",
                    extra={
                        "component": "shutdown_manager",
                        "operation": "signal_handler",
                        "signal_number": signum,
                        "signal_name": "SIGINT",
                        "sigint_count": self._sigint_count
                    }
                )
                print(f"\n⚠️  Press CTRL+C again within {self._sigint_window} seconds to force shutdown")
                return
        
        # Handle other signals normally
        with self._shutdown_lock:
            if self._is_shutting_down:
                logger.warning(
                    "Shutdown already in progress, ignoring signal",
                    extra={
                        "component": "shutdown_manager",
                        "operation": "signal_handler",
                        "signal_number": signum,
                        "signal_name": signal.Signals(signum).name
                    }
                )
                return
            
            self._is_shutting_down = True
        
        # Determine shutdown reason
        if signum == signal.SIGINT:
            reason = ShutdownReason.SIGNAL_INTERRUPT
        elif signum == signal.SIGTERM:
            reason = ShutdownReason.SIGNAL_TERMINATE
        elif hasattr(signal, 'SIGUSR1') and signum == getattr(signal, 'SIGUSR1', None):
            reason = ShutdownReason.MANUAL_SHUTDOWN
        else:
            reason = ShutdownReason.UNKNOWN
        
        # Start shutdown monitoring
        signal_info = {
            "signal_number": signum,
            "signal_name": signal.Signals(signum).name,
            "reason": reason.value
        }
        shutdown_monitor.start_shutdown_tracking(signal_info)
        shutdown_monitor.record_phase_start(ShutdownPhase.SIGNAL_RECEIVED)
        
        # Create shutdown context
        self._shutdown_context = ShutdownContext(
            reason=reason,
            signal_number=signum,
            graceful_timeout=getattr(settings, "shutdown_graceful_timeout", 30),
            force_timeout=getattr(settings, "shutdown_force_timeout", 5)
        )
        
        logger.warning(
            "Shutdown signal received",
            extra={
                "component": "shutdown_manager",
                "operation": "signal_received",
                "signal_number": signum,
                "signal_name": signal.Signals(signum).name,
                "shutdown_reason": reason.value,
                "graceful_timeout": self._shutdown_context.graceful_timeout,
                "force_timeout": self._shutdown_context.force_timeout
            }
        )
        
        # Trigger shutdown event
        self._shutdown_event.set()
    
    def _force_cold_shutdown(self):
        """Force immediate cold shutdown without graceful cleanup."""
        logger.critical(
            "Initiating cold shutdown - bypassing graceful cleanup",
            extra={
                "component": "shutdown_manager",
                "operation": "cold_shutdown",
                "reason": "double_ctrlc"
            }
        )
        
        # Log critical shutdown event
        shutdown_monitor.record_phase_start(ShutdownPhase.FORCE_SHUTDOWN)
        
        # Force exit without cleanup
        print("\n🛑 Cold shutdown initiated - exiting immediately")
        sys.exit(1)
    
    def register_cleanup_handler(self, handler: Callable, is_async: bool = False):
        """
        Register a cleanup handler to be called during shutdown.
        
        Args:
            handler: Function to call during cleanup
            is_async: Whether the handler is async
        """
        if is_async:
            self._async_cleanup_handlers.append(handler)
        else:
            self._cleanup_handlers.append(handler)
        
        logger.debug(
            "Cleanup handler registered",
            extra={
                "component": "shutdown_manager",
                "operation": "register_cleanup",
                "handler_name": handler.__name__,
                "is_async": is_async,
                "total_handlers": len(self._cleanup_handlers) + len(self._async_cleanup_handlers)
            }
        )
    
    def unregister_cleanup_handler(self, handler: Callable):
        """Unregister a cleanup handler."""
        try:
            self._cleanup_handlers.remove(handler)
            logger.debug(
                "Cleanup handler unregistered",
                extra={
                    "component": "shutdown_manager",
                    "operation": "unregister_cleanup",
                    "handler_name": handler.__name__
                }
            )
        except ValueError:
            pass
        
        try:
            self._async_cleanup_handlers.remove(handler)
            logger.debug(
                "Async cleanup handler unregistered",
                extra={
                    "component": "shutdown_manager",
                    "operation": "unregister_cleanup_async",
                    "handler_name": handler.__name__
                }
            )
        except ValueError:
            pass
    
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        return self._shutdown_event.is_set()
    
    def wait_for_shutdown(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for shutdown signal.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if shutdown was requested, False if timeout occurred
        """
        return self._shutdown_event.wait(timeout)
    
    async def perform_graceful_shutdown(self) -> ShutdownContext:
        """
        Perform graceful shutdown with all registered cleanup handlers.
        
        Returns:
            ShutdownContext with results of shutdown process
        """
        if not self._shutdown_context:
            self._shutdown_context = ShutdownContext(
                reason=ShutdownReason.MANUAL_SHUTDOWN
            )
        
        context = self._shutdown_context
        start_time = time.time()
        
        # Start monitoring if not already started
        if not shutdown_monitor.get_current_status()["is_tracking"]:
            signal_info = {"reason": context.reason.value}
            shutdown_monitor.start_shutdown_tracking(signal_info)
        
        logger.warning(
            "Starting graceful shutdown",
            extra={
                "component": "shutdown_manager",
                "operation": "graceful_shutdown_start",
                "reason": context.reason.value,
                "graceful_timeout": context.graceful_timeout,
                "force_timeout": context.force_timeout,
                "total_handlers": len(self._cleanup_handlers) + len(self._async_cleanup_handlers)
            }
        )
        
        # Phase 1: Synchronous cleanup handlers
        shutdown_monitor.record_phase_start(ShutdownPhase.SYNC_CLEANUP_START)
        
        if self._cleanup_handlers:
            logger.info(
                "Executing synchronous cleanup handlers",
                extra={
                    "component": "shutdown_manager",
                    "operation": "sync_cleanup_start",
                    "handler_count": len(self._cleanup_handlers)
                }
            )
            
            for handler in self._cleanup_handlers:
                handler_start = time.time()
                try:
                    handler()
                    handler_time = time.time() - handler_start
                    
                    context.cleanup_tasks.append(f"{handler.__name__}: {handler_time:.3f}s")
                    shutdown_monitor.record_cleanup_task(handler.__name__, handler_time, True)
                    
                    logger.debug(
                        "Synchronous cleanup handler completed",
                        extra={
                            "component": "shutdown_manager",
                            "operation": "sync_cleanup_complete",
                            "handler_name": handler.__name__,
                            "execution_time": handler_time
                        }
                    )
                    
                except Exception as e:
                    handler_time = time.time() - handler_start
                    error_msg = f"{handler.__name__}: {str(e)}"
                    context.errors.append(error_msg)
                    shutdown_monitor.record_cleanup_task(handler.__name__, handler_time, False)
                    shutdown_monitor.record_error(error_msg, {"handler": handler.__name__})
                    
                    logger.error(
                        "Synchronous cleanup handler failed",
                        extra={
                            "component": "shutdown_manager",
                            "operation": "sync_cleanup_error",
                            "handler_name": handler.__name__,
                            "error": str(e),
                            "error_type": type(e).__name__
                        }
                    )
        
        # Phase 2: Asynchronous cleanup handlers
        if self._async_cleanup_handlers:
            logger.info(
                "Executing asynchronous cleanup handlers",
                extra={
                    "component": "shutdown_manager",
                    "operation": "async_cleanup_start",
                    "handler_count": len(self._async_cleanup_handlers)
                }
            )
            
            # Create tasks for all async handlers
            tasks = []
            for handler in self._async_cleanup_handlers:
                task = asyncio.create_task(self._execute_async_handler(handler, context))
                tasks.append(task)
            
            # Wait for all tasks with timeout
            if tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=context.graceful_timeout
                    )
                except asyncio.TimeoutError:
                    context.warnings.append(f"Async cleanup timeout after {context.graceful_timeout}s")
                    logger.warning(
                        "Async cleanup timeout",
                        extra={
                            "component": "shutdown_manager",
                            "operation": "async_cleanup_timeout",
                            "timeout": context.graceful_timeout
                        }
                    )
        
        # Complete shutdown monitoring
        shutdown_monitor.record_phase_complete(ShutdownPhase.SYNC_CLEANUP_COMPLETE)
        shutdown_monitor.record_phase_start(ShutdownPhase.ASYNC_CLEANUP_START)
        
        # Phase 2: Asynchronous cleanup handlers
        if self._async_cleanup_handlers:
            logger.info(
                "Executing asynchronous cleanup handlers",
                extra={
                    "component": "shutdown_manager",
                    "operation": "async_cleanup_start",
                    "handler_count": len(self._async_cleanup_handlers)
                }
            )
            
            # Create tasks for all async handlers
            tasks = []
            for handler in self._async_cleanup_handlers:
                task = asyncio.create_task(self._execute_async_handler(handler, context))
                tasks.append(task)
            
            # Wait for all tasks with timeout
            if tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=context.graceful_timeout
                    )
                except asyncio.TimeoutError:
                    context.warnings.append(f"Async cleanup timeout after {context.graceful_timeout}s")
                    shutdown_monitor.record_warning(f"Async cleanup timeout after {context.graceful_timeout}s")
                    logger.warning(
                        "Async cleanup timeout",
                        extra={
                            "component": "shutdown_manager",
                            "operation": "async_cleanup_timeout",
                            "timeout": context.graceful_timeout
                        }
                    )
        
        shutdown_monitor.record_phase_complete(ShutdownPhase.ASYNC_CLEANUP_COMPLETE)
        shutdown_monitor.record_phase_start(ShutdownPhase.SHUTDOWN_COMPLETE)
        
        # Calculate total shutdown time
        total_time = time.time() - start_time
        
        # Complete shutdown monitoring
        shutdown_monitor.record_phase_complete(ShutdownPhase.SHUTDOWN_COMPLETE)
        shutdown_monitor.complete_shutdown_tracking()
        
        logger.warning(
            "Graceful shutdown completed",
            extra={
                "component": "shutdown_manager",
                "operation": "graceful_shutdown_complete",
                "total_time": total_time,
                "cleanup_tasks": len(context.cleanup_tasks),
                "errors": len(context.errors),
                "warnings": len(context.warnings),
                "reason": context.reason.value
            }
        )
        
        return context
    
    async def _execute_async_handler(self, handler: Callable, context: ShutdownContext):
        """Execute an async cleanup handler with error handling."""
        try:
            handler_start = time.time()
            await handler()
            handler_time = time.time() - handler_start
            
            context.cleanup_tasks.append(f"{handler.__name__}: {handler_time:.3f}s")
            
            logger.debug(
                "Asynchronous cleanup handler completed",
                extra={
                    "component": "shutdown_manager",
                    "operation": "async_cleanup_complete",
                    "handler_name": handler.__name__,
                    "execution_time": handler_time
                }
            )
            
        except Exception as e:
            error_msg = f"{handler.__name__}: {str(e)}"
            context.errors.append(error_msg)
            
            logger.error(
                "Asynchronous cleanup handler failed",
                extra={
                    "component": "shutdown_manager",
                    "operation": "async_cleanup_error",
                    "handler_name": handler.__name__,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
    
    def force_shutdown(self):
        """Force immediate shutdown without cleanup."""
        logger.critical(
            "Force shutdown initiated",
            extra={
                "component": "shutdown_manager",
                "operation": "force_shutdown",
                "reason": "timeout_or_emergency"
            }
        )
        
        # Restore original signal handlers
        self._restore_signal_handlers()
        
        # Exit immediately
        sys.exit(1)
    
    def _restore_signal_handlers(self):
        """Restore original signal handlers."""
        try:
            for signum, handler in self._original_signal_handlers.items():
                if handler is not None:
                    signal.signal(signum, handler)
            
            logger.debug(
                "Original signal handlers restored",
                extra={
                    "component": "shutdown_manager",
                    "operation": "restore_signals"
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to restore signal handlers",
                extra={
                    "component": "shutdown_manager",
                    "operation": "restore_signals",
                    "error": str(e)
                }
            )
    
    def get_shutdown_status(self) -> Dict[str, Any]:
        """Get current shutdown status for monitoring."""
        return {
            "is_shutting_down": self._is_shutting_down,
            "shutdown_requested": self._shutdown_event.is_set(),
            "cleanup_handlers_count": len(self._cleanup_handlers),
            "async_cleanup_handlers_count": len(self._async_cleanup_handlers),
            "shutdown_context": {
                "reason": self._shutdown_context.reason.value if self._shutdown_context else None,
                "signal_number": self._shutdown_context.signal_number if self._shutdown_context else None,
                "start_time": self._shutdown_context.start_time if self._shutdown_context else None
            } if self._shutdown_context else None
        }


# Global shutdown manager instance
shutdown_manager = GracefulShutdownManager()


@asynccontextmanager
async def shutdown_context():
    """
    Context manager for graceful shutdown operations.
    
    Usage:
        async with shutdown_context():
            # Application code here
            pass
    """
    try:
        yield
    finally:
        if shutdown_manager.is_shutdown_requested():
            await shutdown_manager.perform_graceful_shutdown()


def register_default_cleanup_handlers():
    """Register default cleanup handlers for common resources."""
    
    # Database cleanup
    def cleanup_database():
        try:
            from .database import close_database_connections
            close_database_connections()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Failed to close database connections: {e}")
    
    # Celery cleanup
    def cleanup_celery():
        try:
            from ..tasks.celery_app import celery_app
            celery_app.control.shutdown()
            logger.info("Celery workers shutdown")
        except Exception as e:
            logger.error(f"Failed to shutdown Celery workers: {e}")
    
    # Async Celery cleanup
    async def async_cleanup_celery():
        try:
            from ..tasks.celery_app import celery_app
            # Wait for active tasks to complete
            inspect = celery_app.control.inspect()
            active_tasks = inspect.active()
            
            if active_tasks:
                logger.info(f"Waiting for {len(active_tasks)} active Celery tasks to complete")
                # Give tasks time to complete gracefully
                await asyncio.sleep(5)
            
            celery_app.control.shutdown()
            logger.info("Celery workers shutdown completed")
        except Exception as e:
            logger.error(f"Failed to shutdown Celery workers: {e}")
    
    # File cleanup
    def cleanup_files():
        try:
            import tempfile
            import shutil
            # Clean up temporary files
            tempfile._cleanup()  # type: ignore
            logger.info("Temporary files cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup temporary files: {e}")
    
    # Register handlers
    shutdown_manager.register_cleanup_handler(cleanup_database)
    shutdown_manager.register_cleanup_handler(cleanup_celery)
    shutdown_manager.register_cleanup_handler(cleanup_files)
    shutdown_manager.register_cleanup_handler(async_cleanup_celery, is_async=True)
    
    logger.info(
        "Default cleanup handlers registered",
        extra={
            "component": "shutdown_manager",
            "operation": "register_default_handlers",
            "handlers": ["database", "celery", "files", "async_celery"]
        }
    )


# Register default handlers on module import
register_default_cleanup_handlers() 