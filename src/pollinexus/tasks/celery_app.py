"""
Celery application configuration for Pollinexus.

This module configures the Celery application with comprehensive
logging, monitoring, and error handling.
"""

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure, task_success
from celery.utils.log import get_task_logger
import time
import uuid
from typing import Dict, Any

from ..core.config import settings
from ..core.logging import logger, correlation_id
from ..core.metrics import performance_monitor
from ..core.error_tracking import error_tracker

# Create Celery app
celery_app = Celery(
    "pollinexus",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        'pollinexus.tasks.analysis',
        'pollinexus.tasks.visualization',
        'pollinexus.tasks.data_processing'
    ]
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Task settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    task_always_eager=False,  # Set to True for testing
    
    # Result settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Queue settings
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Logging
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
    
    # Security
    security_key=settings.api_secret_key,
    
    # Performance
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Error handling
    task_remote_tracebacks=True,
    task_ignore_result=False,
)

# Task routing
celery_app.conf.task_routes = {
    'pollinexus.tasks.analysis.*': {'queue': 'analysis'},
    'pollinexus.tasks.visualization.*': {'queue': 'visualization'},
    'pollinexus.tasks.data_processing.*': {'queue': 'data_processing'},
}

# Task annotations for monitoring
celery_app.conf.task_annotations = {
    '*': {
        'rate_limit': '10/m',  # 10 tasks per minute
        'time_limit': 1800,    # 30 minutes
        'soft_time_limit': 1500,  # 25 minutes
    },
    'pollinexus.tasks.analysis.analyze_bee_preferences': {
        'rate_limit': '5/m',   # 5 analysis tasks per minute
        'time_limit': 3600,    # 1 hour for complex analysis
    },
    'pollinexus.tasks.visualization.create_visualization': {
        'rate_limit': '20/m',  # 20 visualization tasks per minute
        'time_limit': 900,     # 15 minutes for visualization
    },
}

# Custom task logger
task_logger = get_task_logger(__name__)


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extras):
    """Handle task pre-run events with logging."""
    
    # Generate correlation ID for task tracking
    task_correlation_id = str(uuid.uuid4())
    correlation_id.set(task_correlation_id)
    
    logger.info(
        "Task started",
        task_id=task_id,
        task_name=task.name,
        correlation_id=task_correlation_id,
        args=str(args)[:200] if args else None,  # Truncate long args
        kwargs=str(kwargs)[:200] if kwargs else None,  # Truncate long kwargs
        operation="celery_task_start"
    )
    
    # Store start time for performance tracking
    task.start_time = time.time()
    task.correlation_id = task_correlation_id


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **extras):
    """Handle task post-run events with logging."""
    
    # Calculate execution time
    execution_time = time.time() - getattr(task, 'start_time', time.time())
    
    logger.info(
        "Task completed",
        task_id=task_id,
        task_name=task.name,
        correlation_id=getattr(task, 'correlation_id', None),
        state=state,
        execution_time=execution_time,
        operation="celery_task_complete"
    )
    
    # Log performance metrics
    performance_monitor.log_operation_time(
        operation=f"celery_{task.name}",
        duration=execution_time,
        task_id=task_id,
        state=state
    )
    
    # Clear correlation ID
    correlation_id.set(None)


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Handle successful task completion."""
    
    task_id = kwargs.get('task_id')
    task_name = kwargs.get('task_name')
    
    logger.info(
        "Task succeeded",
        task_id=task_id,
        task_name=task_name,
        correlation_id=correlation_id.get(),
        result_size=len(str(result)) if result else 0,
        operation="celery_task_success"
    )


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **extras):
    """Handle task failure with comprehensive error tracking."""
    
    task_name = extras.get('task_name', 'unknown')
    
    logger.error(
        "Task failed",
        task_id=task_id,
        task_name=task_name,
        correlation_id=correlation_id.get(),
        exception=str(exception),
        exception_type=type(exception).__name__,
        args=str(args)[:200] if args else None,
        kwargs=str(kwargs)[:200] if kwargs else None,
        operation="celery_task_failure"
    )
    
    # Track error for monitoring
    error_tracker.track_error(
        error_type="celery_task_failure",
        error=exception,
        context={
            'task_id': task_id,
            'task_name': task_name,
            'args': args,
            'kwargs': kwargs,
            'traceback': traceback
        }
    )


# Health check task
@celery_app.task(bind=True, name='pollinexus.tasks.health_check')
def health_check(self):
    """Health check task for monitoring Celery workers."""
    
    logger.info(
        "Health check task executed",
        task_id=self.request.id,
        operation="celery_health_check"
    )
    
    return {
        'status': 'healthy',
        'task_id': self.request.id,
        'worker': self.request.hostname,
        'timestamp': time.time()
    }


# Task monitoring utilities
def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get detailed task status and information."""
    
    try:
        result = celery_app.AsyncResult(task_id)
        
        status_info = {
            'task_id': task_id,
            'status': result.status,
            'successful': result.successful(),
            'failed': result.failed(),
            'ready': result.ready(),
            'info': result.info if result.ready() else None,
            'traceback': result.traceback if result.failed() else None,
            'date_done': result.date_done.isoformat() if result.date_done else None,
        }
        
        logger.debug(
            "Task status retrieved",
            task_id=task_id,
            status=result.status,
            operation="celery_task_status"
        )
        
        return status_info
        
    except Exception as e:
        logger.error(
            "Failed to get task status",
            task_id=task_id,
            error=str(e),
            operation="celery_task_status"
        )
        raise


def cancel_task(task_id: str) -> bool:
    """Cancel a running task."""
    
    try:
        result = celery_app.AsyncResult(task_id)
        
        if result.state in ['PENDING', 'STARTED']:
            result.revoke(terminate=True)
            
            logger.info(
                "Task cancelled",
                task_id=task_id,
                state=result.state,
                operation="celery_task_cancel"
            )
            
            return True
        else:
            logger.warning(
                "Cannot cancel task - not in cancellable state",
                task_id=task_id,
                state=result.state,
                operation="celery_task_cancel"
            )
            
            return False
            
    except Exception as e:
        logger.error(
            "Failed to cancel task",
            task_id=task_id,
            error=str(e),
            operation="celery_task_cancel"
        )
        raise


def get_worker_stats() -> Dict[str, Any]:
    """Get Celery worker statistics."""
    
    try:
        inspect = celery_app.control.inspect()
        
        stats = {
            'active_tasks': inspect.active(),
            'registered_tasks': inspect.registered(),
            'worker_stats': inspect.stats(),
            'timestamp': time.time()
        }
        
        logger.debug(
            "Worker statistics retrieved",
            operation="celery_worker_stats"
        )
        
        return stats
        
    except Exception as e:
        logger.error(
            "Failed to get worker statistics",
            error=str(e),
            operation="celery_worker_stats"
        )
        raise


# Task result backend utilities
def cleanup_old_results(hours_old: int = 24) -> int:
    """Clean up old task results."""
    
    try:
        # This would depend on the specific result backend implementation
        # For now, we'll log the cleanup request
        logger.info(
            "Cleanup old results requested",
            hours_old=hours_old,
            operation="celery_cleanup_results"
        )
        
        # TODO: Implement actual cleanup based on result backend
        # For Redis: Use TTL-based cleanup
        # For database: Delete old records
        
        return 0
        
    except Exception as e:
        logger.error(
            "Failed to cleanup old results",
            error=str(e),
            operation="celery_cleanup_results"
        )
        raise


if __name__ == '__main__':
    celery_app.start() 