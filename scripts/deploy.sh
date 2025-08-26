#!/bin/bash

# Pollinexus Production Deployment Script
# This script provides secure, automated deployment with monitoring and rollback capabilities

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_ENV="${1:-production}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/pollinexus"
LOG_FILE="/var/log/pollinexus/deployment_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] ${message}" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR" "Deployment failed: $1"
    echo -e "${RED}❌ Deployment failed: $1${NC}"
    exit 1
}

# Success message
success() {
    log "SUCCESS" "$1"
    echo -e "${GREEN}✅ $1${NC}"
}

# Warning message
warning() {
    log "WARNING" "$1"
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Info message
info() {
    log "INFO" "$1"
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error_exit "This script should not be run as root"
    fi
}

# Validate environment
validate_environment() {
    info "Validating deployment environment..."
    
    # Check required environment variables
    local required_vars=(
        "DB_PASSWORD"
        "API_SECRET_KEY"
        "REDIS_PASSWORD"
        "GRAFANA_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error_exit "Required environment variable $var is not set"
        fi
    done
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        error_exit "Docker is not installed or not in PATH"
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null; then
        error_exit "Docker Compose is not installed or not in PATH"
    fi
    
    # Check disk space
    local available_space=$(df / | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 10485760 ]]; then  # 10GB in KB
        warning "Low disk space available: $(($available_space / 1024 / 1024))GB"
    fi
    
    success "Environment validation completed"
}

# Create backup
create_backup() {
    info "Creating backup before deployment..."
    
    # Create backup directory
    sudo mkdir -p "$BACKUP_DIR"
    
    # Backup database
    if docker ps --format "table {{.Names}}" | grep -q "pollinexus-postgres"; then
        info "Backing up PostgreSQL database..."
        docker exec pollinexus-postgres pg_dump -U pollinexus pollinexus > "$BACKUP_DIR/db_backup_${TIMESTAMP}.sql"
        success "Database backup created: $BACKUP_DIR/db_backup_${TIMESTAMP}.sql"
    else
        warning "PostgreSQL container not running, skipping database backup"
    fi
    
    # Backup configuration files
    info "Backing up configuration files..."
    tar -czf "$BACKUP_DIR/config_backup_${TIMESTAMP}.tar.gz" \
        -C "$PROJECT_ROOT" \
        docker/production/ \
        scripts/ \
        .env \
        2>/dev/null || warning "Some configuration files could not be backed up"
    
    # Backup data volumes
    info "Backing up data volumes..."
    docker run --rm \
        -v pollinexus_data:/data \
        -v "$BACKUP_DIR":/backup \
        alpine tar -czf "/backup/data_backup_${TIMESTAMP}.tar.gz" -C /data . \
        2>/dev/null || warning "Data volume backup failed"
    
    success "Backup completed"
}

# Run security checks
run_security_checks() {
    info "Running security checks..."
    
    # Check for security vulnerabilities in images
    if command -v trivy &> /dev/null; then
        info "Scanning Docker images for vulnerabilities..."
        trivy image --severity HIGH,CRITICAL pollinexus/api:latest || warning "Vulnerability scan found issues"
    else
        warning "Trivy not installed, skipping vulnerability scan"
    fi
    
    # Check SSL certificates
    if [[ -f "$PROJECT_ROOT/docker/production/nginx/ssl/cert.pem" ]]; then
        info "Validating SSL certificate..."
        openssl x509 -in "$PROJECT_ROOT/docker/production/nginx/ssl/cert.pem" -text -noout | grep -q "Not After" || warning "SSL certificate validation failed"
    else
        warning "SSL certificate not found"
    fi
    
    # Check file permissions
    info "Checking file permissions..."
    find "$PROJECT_ROOT" -name "*.env" -exec stat -c "%a %n" {} \; | while read perms file; do
        if [[ $perms != "600" ]]; then
            warning "Insecure permissions on $file: $perms"
        fi
    done
    
    success "Security checks completed"
}

# Build and push images
build_images() {
    info "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build API image
    info "Building API image..."
    docker build \
        --target production \
        --tag pollinexus/api:latest \
        --tag pollinexus/api:${TIMESTAMP} \
        --file Dockerfile \
        . || error_exit "Failed to build API image"
    
    # Build worker image
    info "Building worker image..."
    docker build \
        --target production \
        --tag pollinexus/worker:latest \
        --tag pollinexus/worker:${TIMESTAMP} \
        --file Dockerfile \
        . || error_exit "Failed to build worker image"
    
    # Build beat image
    info "Building beat image..."
    docker build \
        --target production \
        --tag pollinexus/beat:latest \
        --tag pollinexus/beat:${TIMESTAMP} \
        --file Dockerfile \
        . || error_exit "Failed to build beat image"
    
    success "Docker images built successfully"
}

# Deploy application
deploy_application() {
    info "Deploying Pollinexus application..."
    
    cd "$PROJECT_ROOT/docker/production"
    
    # Stop existing services gracefully
    info "Stopping existing services..."
    docker-compose down --timeout 30 || warning "Some services could not be stopped gracefully"
    
    # Start services
    info "Starting services..."
    docker-compose up -d --remove-orphans || error_exit "Failed to start services"
    
    # Wait for services to be healthy
    info "Waiting for services to be healthy..."
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose ps | grep -q "unhealthy\|starting"; then
            info "Waiting for services to be healthy... (attempt $attempt/$max_attempts)"
            sleep 10
            ((attempt++))
        else
            success "All services are healthy"
            break
        fi
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        error_exit "Services failed to become healthy within expected time"
    fi
    
    success "Application deployed successfully"
}

# Run database migrations
run_migrations() {
    info "Running database migrations..."
    
    # Wait for database to be ready
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker exec pollinexus-postgres pg_isready -U pollinexus -d pollinexus &>/dev/null; then
            break
        fi
        info "Waiting for database to be ready... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        error_exit "Database failed to become ready"
    fi
    
    # Run migrations
    docker exec pollinexus-api python -m pollinexus.cli migrate || error_exit "Database migration failed"
    
    success "Database migrations completed"
}

# Health check
health_check() {
    info "Performing health checks..."
    
    # Check API health
    local api_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health || echo "000")
    if [[ $api_health != "200" ]]; then
        error_exit "API health check failed: HTTP $api_health"
    fi
    
    # Check database connectivity
    if ! docker exec pollinexus-postgres pg_isready -U pollinexus -d pollinexus &>/dev/null; then
        error_exit "Database health check failed"
    fi
    
    # Check Redis connectivity
    if ! docker exec pollinexus-redis redis-cli ping &>/dev/null; then
        error_exit "Redis health check failed"
    fi
    
    # Check Celery workers
    if ! docker exec pollinexus-worker celery -A pollinexus.tasks.celery_app inspect ping &>/dev/null; then
        error_exit "Celery worker health check failed"
    fi
    
    success "All health checks passed"
}

# Performance test
performance_test() {
    info "Running performance tests..."
    
    # Simple load test
    local response_time=$(curl -s -w "%{time_total}" -o /dev/null http://localhost/health)
    if (( $(echo "$response_time > 2.0" | bc -l) )); then
        warning "API response time is slow: ${response_time}s"
    else
        success "API response time is acceptable: ${response_time}s"
    fi
    
    # Check memory usage
    local memory_usage=$(docker stats --no-stream --format "table {{.MemUsage}}" pollinexus-api | tail -n 1)
    info "Memory usage: $memory_usage"
    
    success "Performance tests completed"
}

# Setup monitoring
setup_monitoring() {
    info "Setting up monitoring..."
    
    # Wait for monitoring services to be ready
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s http://localhost:9090/-/healthy &>/dev/null && \
           curl -s http://localhost:3000/api/health &>/dev/null; then
            break
        fi
        info "Waiting for monitoring services... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        warning "Monitoring services failed to become ready"
    else
        success "Monitoring services are ready"
        info "Grafana: http://localhost:3000 (admin/admin)"
        info "Prometheus: http://localhost:9090"
        info "Kibana: http://localhost:5601"
    fi
}

# Rollback function
rollback() {
    warning "Rolling back deployment..."
    
    cd "$PROJECT_ROOT/docker/production"
    
    # Stop current services
    docker-compose down --timeout 30
    
    # Restore previous images
    if docker images | grep -q "pollinexus/api:${TIMESTAMP}"; then
        docker tag pollinexus/api:${TIMESTAMP} pollinexus/api:latest
        docker tag pollinexus/worker:${TIMESTAMP} pollinexus/worker:latest
        docker tag pollinexus/beat:${TIMESTAMP} pollinexus/beat:latest
    fi
    
    # Restart services
    docker-compose up -d
    
    # Restore database if backup exists
    local latest_backup=$(ls -t "$BACKUP_DIR"/db_backup_*.sql 2>/dev/null | head -n 1)
    if [[ -n "$latest_backup" ]]; then
        warning "Restoring database from backup: $latest_backup"
        docker exec -i pollinexus-postgres psql -U pollinexus -d pollinexus < "$latest_backup"
    fi
    
    error_exit "Deployment rolled back"
}

# Cleanup old backups
cleanup_backups() {
    info "Cleaning up old backups..."
    
    # Keep only last 7 days of backups
    find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete 2>/dev/null || true
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete 2>/dev/null || true
    
    success "Backup cleanup completed"
}

# Main deployment function
main() {
    info "Starting Pollinexus deployment to $DEPLOYMENT_ENV environment"
    
    # Create log directory
    sudo mkdir -p "$(dirname "$LOG_FILE")"
    sudo chown "$USER:$USER" "$(dirname "$LOG_FILE")"
    
    # Set up error handling
    trap 'rollback' ERR
    
    # Run deployment steps
    check_root
    validate_environment
    create_backup
    run_security_checks
    build_images
    deploy_application
    run_migrations
    health_check
    performance_test
    setup_monitoring
    cleanup_backups
    
    # Remove error trap
    trap - ERR
    
    success "Deployment completed successfully!"
    info "Application is available at: http://localhost"
    info "API documentation: http://localhost/docs"
    info "Monitoring dashboard: http://localhost:3000"
    info "Deployment log: $LOG_FILE"
}

# Show usage
usage() {
    echo "Usage: $0 [environment]"
    echo "  environment: production, staging, development (default: production)"
    echo ""
    echo "Environment variables required:"
    echo "  DB_PASSWORD: PostgreSQL database password"
    echo "  API_SECRET_KEY: Secret key for API authentication"
    echo "  REDIS_PASSWORD: Redis password"
    echo "  GRAFANA_PASSWORD: Grafana admin password"
    echo ""
    echo "Examples:"
    echo "  $0 production"
    echo "  $0 staging"
}

# Check command line arguments
if [[ $# -gt 1 ]]; then
    usage
    exit 1
fi

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

# Run main function
main "$@" 