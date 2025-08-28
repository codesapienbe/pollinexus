# Graceful Shutdown Implementation

## Overview

The Pollinexus application implements a comprehensive graceful shutdown system that ensures proper cleanup of resources, handles signals appropriately, and provides detailed monitoring and logging for enterprise environments.

## Features

### Signal Handling

- **SIGINT (Ctrl+C)**: Graceful shutdown with cleanup
- **SIGTERM**: Termination request handling
- **SIGUSR1**: Custom graceful shutdown trigger
- **Signal restoration**: Original handlers restored after shutdown

### Resource Cleanup

- **Database connections**: Proper closure of SQLAlchemy sessions and engine disposal
- **Celery workers**: Graceful shutdown of background task workers
- **File handles**: Cleanup of temporary files and open file descriptors
- **Memory cleanup**: Garbage collection and memory management
- **Custom handlers**: Extensible cleanup handler registration system

### Monitoring & Observability

- **Structured logging**: JSON-formatted logs with correlation IDs
- **Metrics collection**: Shutdown duration, success rates, error tracking
- **Phase tracking**: Detailed monitoring of shutdown phases
- **Alerting**: Configurable alerts for long shutdowns or failures
- **API endpoints**: Real-time status and metrics endpoints

### Configuration

- **Graceful timeout**: Configurable timeout for cleanup operations (default: 30s)
- **Force timeout**: Emergency shutdown timeout (default: 5s)
- **Signal handling**: Enable/disable signal interception
- **Log levels**: Configurable logging verbosity

## Usage

### Starting the Application

```bash
# Using CLI
python -m pollinexus.cli run

# Using uvicorn directly
uvicorn pollinexus.api.main:app --host 0.0.0.0 --port 8000
```

### Graceful Shutdown

```bash
# Method 1: Ctrl+C (SIGINT)
# Press Ctrl+C in the terminal where the application is running

# Method 2: SIGTERM
kill -TERM <pid>

# Method 3: SIGUSR1 (custom graceful shutdown)
kill -USR1 <pid>
```

### Force Shutdown

```bash
# Emergency shutdown (use only when graceful shutdown fails)
kill -KILL <pid>
```

## API Endpoints

### Shutdown Status

```http
GET /api/v1/shutdown/status
```

Returns current shutdown manager status and configuration.

**Response:**

```json
{
  "timestamp": 1703123456.789,
  "request_id": "uuid",
  "correlation_id": "uuid",
  "shutdown_status": {
    "is_shutting_down": false,
    "shutdown_requested": false,
    "cleanup_handlers_count": 4,
    "async_cleanup_handlers_count": 1,
    "shutdown_context": null
  },
  "graceful_timeout": 30,
  "force_timeout": 5
}
```

### Shutdown Metrics

```http
GET /api/v1/shutdown/metrics
```

Returns comprehensive shutdown metrics and monitoring data.

**Response:**

```json
{
  "timestamp": 1703123456.789,
  "request_id": "uuid",
  "correlation_id": "uuid",
  "current_status": {
    "is_tracking": false,
    "current_phase": null,
    "elapsed_time": null,
    "metrics_history_count": 5
  },
  "metrics_summary": {
    "total_shutdowns": 5,
    "average_duration": 2.34,
    "min_duration": 1.12,
    "max_duration": 4.56,
    "average_errors": 0.2,
    "average_warnings": 0.4,
    "successful_cleanups": 4,
    "failed_cleanups": 1
  },
  "recent_metrics": [
    {
      "start_time": 1703123450.123,
      "end_time": 1703123452.456,
      "total_duration": 2.333,
      "cleanup_tasks_count": 4,
      "errors_count": 0,
      "warnings_count": 1,
      "signal_info": {
        "signal_number": 2,
        "signal_name": "SIGINT",
        "reason": "signal_interrupt"
      }
    }
  ]
}
```

## Configuration

### Environment Variables

```bash
# Shutdown timeouts
POLLINEXUS_SHUTDOWN_GRACEFUL_TIMEOUT=30
POLLINEXUS_SHUTDOWN_FORCE_TIMEOUT=5

# Signal handling
POLLINEXUS_SHUTDOWN_ENABLE_SIGNAL_HANDLING=true

# Logging
POLLINEXUS_SHUTDOWN_LOG_LEVEL=WARNING
```

### Configuration File

```python
# In config.py
class Settings(BaseSettings):
    # Shutdown settings
    shutdown_graceful_timeout: int = 30  # seconds
    shutdown_force_timeout: int = 5  # seconds
    shutdown_enable_signal_handling: bool = True
    shutdown_log_level: str = "WARNING"
```

## Monitoring & Logging

### Log Structure

All shutdown-related logs use structured JSON format with consistent fields:

```json
{
  "timestamp": "2023-12-21T10:30:45.123Z",
  "level": "WARNING",
  "component": "shutdown_manager",
  "operation": "signal_received",
  "signal_number": 2,
  "signal_name": "SIGINT",
  "shutdown_reason": "signal_interrupt",
  "graceful_timeout": 30,
  "force_timeout": 5,
  "correlation_id": "uuid",
  "request_id": "uuid"
}
```

### Log Levels

- **ERROR**: Shutdown failures, cleanup errors, force shutdowns
- **WARNING**: Signal received, timeout warnings, resource cleanup issues
- **INFO**: Phase transitions, cleanup task completion
- **DEBUG**: Detailed cleanup task execution, monitoring data

### Monitoring Integration

The shutdown system integrates with existing monitoring infrastructure:

- **Health checks**: Shutdown status included in health endpoints
- **Metrics**: Prometheus-compatible metrics for shutdown performance
- **Alerting**: Configurable alerts for shutdown issues
- **Tracing**: Correlation IDs for request tracing

## Custom Cleanup Handlers

### Registering Custom Handlers

```python
from pollinexus.core.shutdown import shutdown_manager

def my_cleanup_handler():
    """Custom cleanup logic."""
    # Cleanup code here
    pass

# Register synchronous handler
shutdown_manager.register_cleanup_handler(my_cleanup_handler)

# Register asynchronous handler
async def my_async_cleanup_handler():
    """Async cleanup logic."""
    # Async cleanup code here
    pass

shutdown_manager.register_cleanup_handler(my_async_cleanup_handler, is_async=True)
```

### Handler Best Practices

1. **Idempotent**: Handlers should be safe to call multiple times
2. **Timeout aware**: Don't block indefinitely
3. **Error handling**: Catch and log exceptions appropriately
4. **Resource cleanup**: Focus on releasing resources, not business logic
5. **Logging**: Use structured logging with appropriate levels

## Troubleshooting

### Common Issues

#### Shutdown Takes Too Long

- Check cleanup handler execution times
- Review database connection cleanup
- Verify Celery worker shutdown
- Monitor resource usage during shutdown

#### Force Shutdown Required

- Check for hanging cleanup handlers
- Review timeout configurations
- Monitor system resources
- Check for deadlocks in cleanup code

#### Missing Cleanup

- Verify handler registration
- Check handler execution logs
- Review error handling in handlers
- Ensure proper exception handling

### Debugging Commands

```bash
# Check shutdown status
curl http://localhost:8000/api/v1/shutdown/status

# Get shutdown metrics
curl http://localhost:8000/api/v1/shutdown/metrics

# Monitor logs
tail -f application.log | grep shutdown

# Check process signals
ps aux | grep pollinexus
```

### Performance Tuning

#### Optimize Cleanup Time

- Reduce database connection pool size
- Optimize Celery worker shutdown
- Minimize file I/O during cleanup
- Use async handlers where appropriate

#### Increase Timeouts

```bash
# For complex cleanup operations
export POLLINEXUS_SHUTDOWN_GRACEFUL_TIMEOUT=60
export POLLINEXUS_SHUTDOWN_FORCE_TIMEOUT=10
```

## Security Considerations

### Signal Handling

- Signal handlers are registered securely
- Original handlers are restored after shutdown
- Signal information is logged for audit purposes

### Resource Cleanup

- Sensitive data is properly cleared from memory
- Database connections are securely closed
- File handles are properly released
- No sensitive information in shutdown logs

### Monitoring

- Shutdown metrics don't expose sensitive data
- Correlation IDs are used for request tracing
- Log sanitization prevents data leakage

## Integration with Deployment

### Docker

```dockerfile
# Use proper signal handling in Docker
STOPSIGNAL SIGTERM
```

### Kubernetes

```yaml
# Pod configuration
spec:
  terminationGracePeriodSeconds: 60
  containers:
  - name: pollinexus
    lifecycle:
      preStop:
        exec:
          command: ["/bin/sh", "-c", "sleep 10"]
```

### Systemd

```ini
[Service]
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=60
```

## Best Practices

### Application Development

1. Register cleanup handlers early in application startup
2. Use async handlers for I/O operations
3. Implement proper error handling in cleanup code
4. Test shutdown scenarios regularly
5. Monitor shutdown performance in production

### Operations

1. Monitor shutdown metrics in production
2. Set up alerts for failed shutdowns
3. Review shutdown logs regularly
4. Test graceful shutdown procedures
5. Document custom cleanup requirements

### Security

1. Review shutdown logs for sensitive data
2. Ensure proper resource cleanup
3. Monitor for unusual shutdown patterns
4. Validate signal handling security
5. Audit cleanup handler security

## Future Enhancements

### Planned Features

- **Distributed shutdown**: Coordinated shutdown across multiple instances
- **Rollback support**: Ability to rollback failed shutdowns
- **Advanced metrics**: More detailed performance analytics
- **Custom signals**: Support for additional signal types
- **Shutdown scheduling**: Planned maintenance shutdowns

### Integration Opportunities

- **Service mesh**: Integration with service mesh shutdown protocols
- **Load balancer**: Coordinated shutdown with load balancers
- **Database**: Advanced database connection management
- **Message queues**: Enhanced message queue cleanup
- **Caching**: Distributed cache cleanup coordination
