# 🚀 Pollinexus Production Deployment Guide

This guide covers deploying Pollinexus API to production with enterprise-grade security, monitoring, and reliability.

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Security Configuration](#security-configuration)
4. [Database Setup](#database-setup)
5. [Docker Deployment](#docker-deployment)
6. [Load Balancer Configuration](#load-balancer-configuration)
7. [Monitoring & Logging](#monitoring--logging)
8. [SSL/TLS Setup](#ssltls-setup)
9. [Backup & Recovery](#backup--recovery)
10. [Maintenance Procedures](#maintenance-procedures)

## ✅ Pre-Deployment Checklist

### Infrastructure Requirements

- [ ] **CPU**: 2+ cores minimum, 4+ recommended
- [ ] **Memory**: 4GB minimum, 8GB+ recommended
- [ ] **Storage**: 50GB+ with SSD for database
- [ ] **Network**: Static IP address and domain name
- [ ] **SSL Certificate**: Valid certificate for HTTPS

### Software Requirements

- [ ] **Docker**: 20.10+ with Docker Compose
- [ ] **PostgreSQL**: 13+ (for production database)
- [ ] **Redis**: 6+ (for Celery broker)
- [ ] **Nginx**: Latest stable (as reverse proxy)

### Security Requirements

- [ ] **Firewall**: Configure iptables/ufw
- [ ] **SSH**: Key-based authentication only
- [ ] **System Updates**: All packages up to date
- [ ] **User Accounts**: Non-root service account

## 🔧 Environment Setup

### 1. Create Production Environment File

```bash
# Copy the example environment file
cp env.example .env

# Edit with production values
nano .env
```

### 2. Essential Production Settings

```bash
# Application
POLLINEXUS_ENVIRONMENT="production"
POLLINEXUS_DEBUG="false"
POLLINEXUS_WORKERS="4"  # Adjust based on CPU cores

# Security
POLLINEXUS_API_SECRET_KEY="$(openssl rand -hex 32)"
POLLINEXUS_JWT_SECRET_KEY="$(openssl rand -hex 32)"

# Database
POLLINEXUS_DATABASE_URL="postgresql://pollinexus:${DB_PASSWORD}@localhost/pollinexus"

# Celery
POLLINEXUS_CELERY_BROKER_URL="redis://localhost:6379/0"
POLLINEXUS_CELERY_RESULT_BACKEND="redis://localhost:6379/0"

# CORS & Security
POLLINEXUS_CORS_ORIGINS='["https://yourdomain.com", "https://www.yourdomain.com"]'
POLLINEXUS_TRUSTED_HOSTS='["yourdomain.com", "www.yourdomain.com"]'

# SSL
POLLINEXUS_USE_SSL="true"
POLLINEXUS_SSL_CERTFILE="/path/to/cert.pem"
POLLINEXUS_SSL_KEYFILE="/path/to/key.pem"
```

## 🔐 Security Configuration

### 1. Generate Secure Keys

```bash
# Generate API secret key
openssl rand -hex 32

# Generate JWT secret key  
openssl rand -hex 32

# Store in environment variables
echo "POLLINEXUS_API_SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "POLLINEXUS_JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env
```

### 2. Configure Firewall

```bash
# Ubuntu/Debian with ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# CentOS/RHEL with firewalld
sudo firewall-cmd --permanent --zone=public --add-service=ssh
sudo firewall-cmd --permanent --zone=public --add-service=http
sudo firewall-cmd --permanent --zone=public --add-service=https
sudo firewall-cmd --reload
```

### 3. Rate Limiting Configuration

```bash
# Adjust based on expected load
POLLINEXUS_RATE_LIMIT_REQUESTS="1000"  # Per minute
POLLINEXUS_RATE_LIMIT_PERIOD="60"
POLLINEXUS_RATE_LIMIT_BURST="2000"
```

## 💾 Database Setup

### 1. Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# CentOS/RHEL
sudo dnf install postgresql-server postgresql-contrib
sudo postgresql-setup --initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### 2. Create Database and User

```sql
-- Connect as postgres user
sudo -u postgres psql

-- Create database and user
CREATE DATABASE pollinexus;
CREATE USER pollinexus WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE pollinexus TO pollinexus;

-- Create extensions if needed
\c pollinexus
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 3. Database Performance Tuning

```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/13/main/postgresql.conf
```

Add these optimizations:

```ini
# Memory settings
shared_buffers = 256MB                  # 25% of RAM for small systems
effective_cache_size = 1GB              # 75% of RAM
work_mem = 4MB                          # For sorting and hash tables
maintenance_work_mem = 64MB             # For VACUUM, CREATE INDEX

# Checkpoint settings
checkpoint_completion_target = 0.7
wal_buffers = 16MB

# Connection settings
max_connections = 200
```

## 🐳 Docker Deployment

### 1. Create Docker Compose Production File

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    build: .
    restart: unless-stopped
    environment:
      - POLLINEXUS_ENVIRONMENT=production
      - POLLINEXUS_DATABASE_URL=postgresql://pollinexus:${DB_PASSWORD}@postgres/pollinexus
      - POLLINEXUS_CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - pollinexus-network
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery-worker:
    build: .
    command: celery -A pollinexus.tasks.celery_app worker --loglevel=info
    restart: unless-stopped
    environment:
      - POLLINEXUS_ENVIRONMENT=production
      - POLLINEXUS_DATABASE_URL=postgresql://pollinexus:${DB_PASSWORD}@postgres/pollinexus
      - POLLINEXUS_CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - pollinexus-network
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs

  celery-beat:
    build: .
    command: celery -A pollinexus.tasks.celery_app beat --loglevel=info
    restart: unless-stopped
    environment:
      - POLLINEXUS_ENVIRONMENT=production
      - POLLINEXUS_DATABASE_URL=postgresql://pollinexus:${DB_PASSWORD}@postgres/pollinexus
      - POLLINEXUS_CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - pollinexus-network

  postgres:
    image: postgres:15
    restart: unless-stopped
    environment:
      - POSTGRES_DB=pollinexus
      - POSTGRES_USER=pollinexus
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - pollinexus-network
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - pollinexus-network
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - api
    networks:
      - pollinexus-network

volumes:
  postgres_data:
  redis_data:

networks:
  pollinexus-network:
    driver: bridge
```

### 2. Optimized Dockerfile for Production

```dockerfile
# Dockerfile.prod
FROM python:3.12-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir build && \
    python -m build && \
    pip install dist/*.whl

FROM python:3.12-slim as production

# Create non-root user
RUN useradd --create-home --shell /bin/bash pollinexus

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set up application
WORKDIR /app
COPY . .
RUN chown -R pollinexus:pollinexus /app

# Switch to non-root user
USER pollinexus

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "30", "pollinexus.api.main:app"]
```

### 3. Deploy with Docker Compose

```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check service status
docker-compose -f docker-compose.prod.yml ps
```

## ⚖️ Load Balancer Configuration

### Nginx Configuration

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream pollinexus_api {
        server api:8000;
        # Add more servers for load balancing
        # server api2:8000;
        # server api3:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

    # SSL configuration
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/certs/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # Rate limiting
        limit_req zone=api burst=20 nodelay;
        limit_req zone=login burst=5 nodelay;

        # API endpoints
        location /api/ {
            proxy_pass http://pollinexus_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health checks (bypass rate limiting)
        location /health {
            proxy_pass http://pollinexus_api;
            proxy_set_header Host $host;
            limit_req off;
        }

        # Static files (if any)
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

## 📊 Monitoring & Logging

### 1. Configure Structured Logging

```bash
# Set logging configuration
POLLINEXUS_LOG_LEVEL="INFO"
POLLINEXUS_LOG_FORMAT="json"
POLLINEXUS_LOG_FILE="/app/logs/application.log"
```

### 2. Log Rotation Setup

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/pollinexus
```

```bash
/app/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

### 3. Health Check Monitoring

Set up external monitoring service to check:

```bash
# Health endpoints
GET https://yourdomain.com/health          # Quick check
GET https://yourdomain.com/health/detailed # Comprehensive check
GET https://yourdomain.com/security/status # Security monitoring
GET https://yourdomain.com/api/v1/metrics  # Performance metrics
```

### 4. Alerting Setup

Configure alerts for:

- **HTTP 5xx errors** > 5% in 5 minutes
- **Response time** > 2 seconds for 95th percentile
- **CPU usage** > 80% for 5 minutes
- **Memory usage** > 90% for 5 minutes
- **Disk space** < 10% remaining
- **Database connections** > 80% of pool

## 🔐 SSL/TLS Setup

### 1. Obtain SSL Certificate

```bash
# Using Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certificate files will be in:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

### 2. Auto-Renewal Setup

```bash
# Add cron job for certificate renewal
sudo crontab -e

# Add this line
0 2 * * * /usr/bin/certbot renew --quiet && systemctl reload nginx
```

### 3. SSL Security Test

```bash
# Test SSL configuration
curl -I https://yourdomain.com

# Use SSL Labs for comprehensive testing
# https://www.ssllabs.com/ssltest/
```

## 💾 Backup & Recovery

### 1. Database Backup Script

```bash
#!/bin/bash
# backup_database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/app/backups"
DB_NAME="pollinexus"

# Create backup
pg_dump -h postgres -U pollinexus -d $DB_NAME | gzip > $BACKUP_DIR/pollinexus_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "pollinexus_*.sql.gz" -mtime +30 -delete

echo "Backup completed: pollinexus_$DATE.sql.gz"
```

### 2. Automated Backup Schedule

```bash
# Add to crontab
0 2 * * * /app/scripts/backup_database.sh >> /app/logs/backup.log 2>&1
```

### 3. Recovery Procedure

```bash
# Restore from backup
gunzip -c /app/backups/pollinexus_YYYYMMDD_HHMMSS.sql.gz | \
    psql -h postgres -U pollinexus -d pollinexus
```

## 🔧 Maintenance Procedures

### 1. Update Deployment

```bash
# Pull latest changes
git pull origin main

# Build new images
docker-compose -f docker-compose.prod.yml build --no-cache

# Rolling update (zero downtime)
docker-compose -f docker-compose.prod.yml up -d --no-deps api
docker-compose -f docker-compose.prod.yml up -d --no-deps celery-worker
```

### 2. Database Migrations

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec api \
    python -c "from pollinexus.models.database import Base; from pollinexus.core.database import engine; Base.metadata.create_all(engine)"
```

### 3. Performance Optimization

```bash
# Analyze database performance
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U pollinexus -d pollinexus -c "SELECT * FROM pg_stat_activity;"

# Optimize database
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U pollinexus -d pollinexus -c "VACUUM ANALYZE;"

# Check API performance
curl -s https://yourdomain.com/api/v1/metrics | jq .
```

### 4. Security Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Scan for vulnerabilities
docker scan pollinexus:latest
```

### 5. Log Analysis

```bash
# Check error rates
tail -f /app/logs/application.log | grep -i error

# Analyze performance
cat /app/logs/application.log | jq 'select(.level=="INFO" and .operation=="api_request_complete") | .process_time' | sort -n

# Monitor security violations
cat /app/logs/application.log | jq 'select(.violation_type)' | head -20
```

## 🚨 Troubleshooting

### Common Issues and Solutions

1. **High Memory Usage**

   ```bash
   # Check memory usage
   docker stats
   
   # Restart services if needed
   docker-compose -f docker-compose.prod.yml restart api
   ```

2. **Database Connection Issues**

   ```bash
   # Check database connectivity
   docker-compose -f docker-compose.prod.yml exec api \
       python -c "from pollinexus.core.database import engine; print(engine.execute('SELECT 1').scalar())"
   ```

3. **SSL Certificate Issues**

   ```bash
   # Check certificate validity
   openssl x509 -in /etc/letsencrypt/live/yourdomain.com/cert.pem -text -noout
   
   # Renew certificate manually
   sudo certbot renew --force-renewal
   ```

4. **Performance Issues**

   ```bash
   # Check system resources
   htop
   iostat 1
   
   # Scale services if needed
   docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=3
   ```

## 📈 Scaling Considerations

### Horizontal Scaling

1. **Load Balancer**: Add more API instances behind load balancer
2. **Database**: Set up read replicas for read-heavy workloads
3. **Celery**: Add more worker nodes for background processing
4. **Caching**: Implement Redis cluster for session storage

### Vertical Scaling

1. **Increase server resources** (CPU, RAM, storage)
2. **Optimize database** configuration
3. **Tune application** settings
4. **Profile and optimize** bottlenecks

---

## 🎯 Production Checklist

Before going live, ensure:

- [ ] All environment variables are set correctly
- [ ] SSL certificates are valid and auto-renewing
- [ ] Database backups are automated
- [ ] Monitoring and alerting are configured
- [ ] Security headers are enabled
- [ ] Rate limiting is active
- [ ] Logs are being collected and rotated
- [ ] Health checks are working
- [ ] Load testing has been performed
- [ ] Incident response procedures are documented

**Your Pollinexus API is now enterprise-ready! 🚀**
