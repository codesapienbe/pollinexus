"""
Security middleware and utilities for Pollinexus API.

This module provides comprehensive security features including rate limiting,
input validation, security headers, and request sanitization.
"""

import time
import ipaddress
import hashlib
import re
from os.path import splitext
from typing import Dict, Optional, Set, List, Any, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import secrets
import threading
from pathlib import Path

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .config import settings
from .logging import logger, request_id, correlation_id


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""
    requests: int
    period: int  # seconds
    burst: int = 0
    key_func: str = "ip"  # ip, user, endpoint


@dataclass
class SecurityViolation:
    """Security violation record."""
    violation_type: str
    client_ip: str
    timestamp: float
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "medium"


class RateLimiter:
    """Token bucket rate limiter with per-client tracking."""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60, burst: int = 200):
        self.max_requests = max_requests
        self.time_window = time_window
        self.burst = burst
        self.clients: Dict[str, deque] = defaultdict(lambda: deque())
        self.lock = threading.Lock()
    
    def is_allowed(self, client_id: str) -> tuple[bool, Dict[str, Any]]:
        """Check if request is allowed for client."""
        with self.lock:
            now = time.time()
            client_requests = self.clients[client_id]
            
            # Remove old requests outside time window
            while client_requests and client_requests[0] <= now - self.time_window:
                client_requests.popleft()
            
            # Check if limit exceeded
            current_requests = len(client_requests)
            
            if current_requests >= self.max_requests:
                # Check burst allowance
                if current_requests >= self.burst:
                    return False, {
                        "current_requests": current_requests,
                        "max_requests": self.max_requests,
                        "burst_limit": self.burst,
                        "time_window": self.time_window,
                        "retry_after": self._get_retry_after(client_requests, now)
                    }
            
            # Allow request and add to tracking
            client_requests.append(now)
            
            return True, {
                "current_requests": current_requests + 1,
                "max_requests": self.max_requests,
                "remaining": max(0, self.max_requests - current_requests - 1),
                "reset_time": int(now + self.time_window)
            }
    
    def _get_retry_after(self, client_requests: deque, now: float) -> int:
        """Calculate retry-after seconds."""
        if not client_requests:
            return self.time_window
        
        oldest_request = client_requests[0]
        return max(1, int(oldest_request + self.time_window - now))
    
    def get_client_stats(self, client_id: str) -> Dict[str, Any]:
        """Get statistics for a client."""
        with self.lock:
            client_requests = self.clients[client_id]
            now = time.time()
            
            # Clean old requests
            while client_requests and client_requests[0] <= now - self.time_window:
                client_requests.popleft()
            
            return {
                "current_requests": len(client_requests),
                "max_requests": self.max_requests,
                "time_window": self.time_window,
                "burst_limit": self.burst
            }
    
    def reset_client(self, client_id: str):
        """Reset rate limit for a client."""
        with self.lock:
            if client_id in self.clients:
                del self.clients[client_id]


class SecurityValidator:
    """Input validation and security checks."""
    
    def __init__(self):
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS
            r'javascript:',  # JavaScript protocol
            r'on\w+\s*=',  # Event handlers
            r'eval\s*\(',  # Code evaluation
            r'union\s+select',  # SQL injection
            r'drop\s+table',  # SQL drop
            r'\.\./.*\.\.',  # Directory traversal
            r'file:///',  # File protocol
            r'data:.*base64',  # Data URLs
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns]
    
    def validate_input(self, value: str) -> tuple[bool, List[str]]:
        """Validate input for security threats."""
        violations = []
        
        if not isinstance(value, str):
            return True, []
        
        # Check for suspicious patterns
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(value):
                violations.append(f"Suspicious pattern detected: {self.suspicious_patterns[i]}")
        
        # Check for excessive length
        if len(value) > 10000:  # 10KB limit
            violations.append("Input exceeds maximum length")
        
        # Check for null bytes
        if '\x00' in value:
            violations.append("Null byte detected")
        
        return len(violations) == 0, violations
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove path separators and dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
        
        # Limit length
        if len(sanitized) > 255:
            name_part, ext = splitext(sanitized)
            sanitized = name_part[:250] + ext
        
        # Ensure it's not empty
        if not sanitized or sanitized in ['.', '..']:
            sanitized = f"file_{secrets.token_hex(4)}"
        
        return sanitized
    
    def validate_ip_address(self, ip: str) -> bool:
        """Validate IP address format."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False


class SecurityMonitor:
    """Monitor and track security violations."""
    
    def __init__(self, max_violations: int = 1000):
        self.max_violations = max_violations
        self.violations: deque = deque(maxlen=max_violations)
        self.blocked_ips: Dict[str, datetime] = {}
        self.violation_counts: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()
        
        # Thresholds for automatic blocking
        self.block_thresholds = {
            "rate_limit": 10,  # Block after 10 rate limit violations
            "input_validation": 5,  # Block after 5 input validation violations
            "authentication": 3,  # Block after 3 auth violations
        }
        self.block_duration = timedelta(minutes=15)
    
    def record_violation(self, violation: SecurityViolation):
        """Record a security violation."""
        with self.lock:
            self.violations.append(violation)
            self.violation_counts[violation.client_ip] += 1
            
            # Check if IP should be blocked
            if (violation.violation_type in self.block_thresholds and 
                self.violation_counts[violation.client_ip] >= self.block_thresholds[violation.violation_type]):
                self._block_ip(violation.client_ip, violation.violation_type)
            
            # Log violation
            logger.warning(
                "Security violation detected",
                extra={
                    "violation_type": violation.violation_type,
                    "client_ip": violation.client_ip,
                    "severity": violation.severity,
                    "details": violation.details
                }
            )
    
    def _block_ip(self, ip: str, reason: str):
        """Block an IP address."""
        self.blocked_ips[ip] = datetime.utcnow() + self.block_duration
        
        logger.error(
            "IP address blocked due to security violations",
            extra={
                "client_ip": ip,
                "reason": reason,
                "block_duration": self.block_duration.total_seconds(),
                "violation_count": self.violation_counts[ip]
            }
        )
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if an IP address is blocked."""
        with self.lock:
            if ip in self.blocked_ips:
                if datetime.utcnow() >= self.blocked_ips[ip]:
                    # Block expired
                    del self.blocked_ips[ip]
                    return False
                return True
            return False
    
    def unblock_ip(self, ip: str):
        """Manually unblock an IP address."""
        with self.lock:
            if ip in self.blocked_ips:
                del self.blocked_ips[ip]
                self.violation_counts[ip] = 0
                logger.info(f"IP address {ip} has been unblocked")
    
    def get_violation_summary(self) -> Dict[str, Any]:
        """Get summary of security violations."""
        with self.lock:
            violation_types = defaultdict(int)
            recent_violations = 0
            now = datetime.utcnow()
            
            # Count violations by type
            for violation in self.violations:
                violation_types[violation.violation_type] += 1
                if now.timestamp() - violation.timestamp < 3600:  # Last hour
                    recent_violations += 1
            
            return {
                "total_violations": len(self.violations),
                "recent_violations": recent_violations,
                "violation_types": dict(violation_types),
                "blocked_ips": len(self.blocked_ips),
                "top_violators": dict(sorted(
                    self.violation_counts.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:10])
            }


class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware."""
    
    def __init__(self, app, rate_limiter: Optional[RateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter(
            max_requests=settings.rate_limit_requests,
            time_window=settings.rate_limit_period,
            burst=settings.rate_limit_burst
        )
        self.security_validator = SecurityValidator()
        self.security_monitor = SecurityMonitor()
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security checks."""
        client_ip = self._get_client_ip(request)
        
        # Skip security checks for local development
        is_local = (
            settings.disable_security_for_local or
            settings.is_development or
            client_ip in ["127.0.0.1", "localhost", "::1"] or
            request.url.hostname in ["localhost", "127.0.0.1", "host.docker.internal"]
        )
        
        if is_local:
            logger.debug(
                "Security checks bypassed for local development",
                extra={
                    "client_ip": client_ip,
                    "hostname": request.url.hostname,
                    "url": str(request.url),
                    "operation": "security_bypass",
                    "reason": "local_development"
                }
            )
            response = await call_next(request)
            # Still add basic security headers for local development
            self._add_basic_security_headers(response)
            return response
        
        # Check if IP is blocked
        if self.security_monitor.is_ip_blocked(client_ip):
            logger.warning(f"Blocked IP {client_ip} attempted access")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Access forbidden", "detail": "IP address blocked"}
            )
        
        # Rate limiting
        allowed, rate_info = self.rate_limiter.is_allowed(client_ip)
        if not allowed:
            # Record rate limit violation
            self.security_monitor.record_violation(SecurityViolation(
                violation_type="rate_limit",
                client_ip=client_ip,
                timestamp=time.time(),
                details=rate_info,
                severity="medium"
            ))
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": "Rate limit exceeded", "retry_after": rate_info["retry_after"]},
                headers={"Retry-After": str(rate_info["retry_after"])}
            )
        
        # Input validation for query parameters
        for param, value in request.query_params.items():
            valid, violations = self.security_validator.validate_input(str(value))
            if not valid:
                self.security_monitor.record_violation(SecurityViolation(
                    violation_type="input_validation",
                    client_ip=client_ip,
                    timestamp=time.time(),
                    details={"parameter": param, "violations": violations},
                    severity="high"
                ))
                
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Invalid input", "detail": "Security validation failed"}
                )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Add security headers
            self._add_security_headers(response, rate_info)
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error"}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _add_security_headers(self, response: Response, rate_info: Dict[str, Any]):
        """Add security headers to response."""
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # Rate limit info
        response.headers["X-RateLimit-Limit"] = str(rate_info["max_requests"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset_time"])

    def _add_basic_security_headers(self, response: Response):
        """Add basic security headers when security is disabled."""
        # Basic security headers only
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"


# Global instances
rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_requests,
    time_window=settings.rate_limit_period,
    burst=settings.rate_limit_burst
)

security_validator = SecurityValidator()
security_monitor = SecurityMonitor()


def create_security_middleware(app):
    """Create and configure security middleware."""
    return SecurityMiddleware(app, rate_limiter)


def calculate_file_checksum(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate checksum for {file_path}: {e}")
        raise ValueError(f"Failed to calculate file checksum: {str(e)}")


def calculate_upload_checksum(upload_file) -> str:
    """Calculate SHA-256 checksum of an uploaded file."""
    sha256_hash = hashlib.sha256()
    
    try:
        # Reset file pointer to beginning
        upload_file.file.seek(0)
        
        # Read file in chunks to handle large files efficiently
        for chunk in iter(lambda: upload_file.file.read(4096), b""):
            sha256_hash.update(chunk)
        
        # Reset file pointer for later use
        upload_file.file.seek(0)
        
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate checksum for uploaded file: {e}")
        raise ValueError(f"Failed to calculate upload checksum: {str(e)}")


# Export main components
__all__ = [
    "RateLimiter",
    "SecurityValidator", 
    "SecurityMonitor",
    "SecurityMiddleware",
    "SecurityViolation",
    "RateLimitRule",
    "rate_limiter",
    "security_validator",
    "security_monitor",
    "create_security_middleware"
] 