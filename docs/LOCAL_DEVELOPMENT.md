# Local Development Security Settings

## Overview

Pollinexus API includes comprehensive security middleware for production environments, but these features can be disabled for local development to improve development experience and reduce complexity.

## Security Features Disabled in Local Development

When running locally, the following security features are automatically disabled:

### 1. Rate Limiting

- **Production**: Limits requests per IP address (default: 100 requests/minute)
- **Local**: No rate limiting applied
- **Benefit**: Faster development and testing without hitting rate limits

### 2. IP Blocking

- **Production**: Blocks IPs with repeated security violations
- **Local**: No IP blocking
- **Benefit**: No risk of accidentally blocking your development machine

### 3. Input Validation

- **Production**: Strict validation of query parameters and request data
- **Local**: Basic validation only
- **Benefit**: Easier testing with various input formats

### 4. Security Headers

- **Production**: Full security headers (CSP, HSTS, etc.)
- **Local**: Basic security headers only
- **Benefit**: Faster response times and easier debugging

## Configuration

### Automatic Detection

The API automatically detects local development based on:

1. **Environment Setting**: `POLLINEXUS_ENVIRONMENT="development"`
2. **Security Flag**: `POLLINEXUS_DISABLE_SECURITY_FOR_LOCAL="true"`
3. **Client IP**: Requests from `127.0.0.1`, `localhost`, `::1`
4. **Hostname**: Requests to `localhost`, `127.0.0.1`, `host.docker.internal`

### Environment Variables

```bash
# Enable local development mode
POLLINEXUS_ENVIRONMENT="development"
POLLINEXUS_DISABLE_SECURITY_FOR_LOCAL="true"

# Optional: Enable debug mode for more verbose logging
POLLINEXUS_DEBUG="true"
```

### Configuration File (.env)

```bash
# Copy the example environment file
cp env.example .env

# The following settings are already configured for local development:
POLLINEXUS_ENVIRONMENT="development"
POLLINEXUS_DISABLE_SECURITY_FOR_LOCAL="true"
POLLINEXUS_DEBUG="true"
```

## Logging

When security features are disabled for local development, you'll see log messages like:

```json
{
  "timestamp": "2025-08-28T13:45:00.000Z",
  "level": "INFO",
  "message": "Security middleware disabled for local development",
  "environment": "development",
  "disable_security_for_local": true,
  "is_development": true,
  "operation": "app_startup"
}
```

For individual requests:

```json
{
  "timestamp": "2025-08-28T13:45:01.000Z",
  "level": "DEBUG",
  "message": "Security checks bypassed for local development",
  "client_ip": "127.0.0.1",
  "hostname": "localhost",
  "url": "http://localhost:8000/api/v1/datasets/",
  "operation": "security_bypass",
  "reason": "local_development"
}
```

## Production vs Local Development

| Feature | Production | Local Development |
|---------|------------|-------------------|
| Rate Limiting | ✅ Enabled | ❌ Disabled |
| IP Blocking | ✅ Enabled | ❌ Disabled |
| Input Validation | ✅ Strict | ⚠️ Basic |
| Security Headers | ✅ Full | ⚠️ Basic |
| CORS | ✅ Restricted | ✅ Open |
| Trusted Hosts | ✅ Enforced | ❌ Disabled |

## Security Considerations

### For Local Development

- Security middleware is disabled to improve development experience
- Basic security headers are still applied
- CORS is configured to allow localhost origins
- No sensitive data should be used in local development

### For Production

- All security features are automatically enabled
- Rate limiting, IP blocking, and input validation are active
- Full security headers are applied
- Trusted hosts are enforced

## Troubleshooting

### Security Middleware Still Active

If you're still seeing security middleware in local development:

1. **Check Environment Variables**:

   ```bash
   echo $POLLINEXUS_ENVIRONMENT
   echo $POLLINEXUS_DISABLE_SECURITY_FOR_LOCAL
   ```

2. **Verify .env File**:

   ```bash
   cat .env | grep -E "(ENVIRONMENT|DISABLE_SECURITY)"
   ```

3. **Check Application Logs**:
   Look for startup messages indicating security middleware status

### Rate Limiting Still Applied

If you're hitting rate limits locally:

1. **Restart the Application**: Configuration changes require restart
2. **Check Client IP**: Ensure requests are coming from localhost
3. **Verify Settings**: Confirm `disable_security_for_local` is set to `true`

## Best Practices

### Development

- Always use `POLLINEXUS_ENVIRONMENT="development"` for local work
- Keep `POLLINEXUS_DISABLE_SECURITY_FOR_LOCAL="true"` for faster development
- Use debug logging to understand security bypass behavior

### Testing

- Test security features in a staging environment
- Use production-like settings for integration testing
- Verify security middleware works correctly before deployment

### Production

- Never disable security features in production
- Use `POLLINEXUS_ENVIRONMENT="production"`
- Set `POLLINEXUS_DISABLE_SECURITY_FOR_LOCAL="false"`
- Monitor security logs for violations

## Related Documentation

- [Security Implementation](./SECURITY.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Configuration Guide](./CONFIGURATION.md)
