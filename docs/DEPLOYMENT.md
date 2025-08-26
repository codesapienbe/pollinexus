# Pollinexus API Deployment Guide

Simple deployment guide for the Pollinexus API using Docker Compose and `uv`.

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/codesapienbe/pollinexus.git
cd pollinexus
```

### 2. Deploy with Docker Compose

```bash
# Start all services
docker-compose up -d

# Build and start services (if you need to rebuild)
docker-compose up -d --build
```

### 3. Verify Deployment

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

## Docker Compose Services

The application uses a simple Docker Compose setup with the following services:

- **api**: FastAPI application (exposed on port 8000)
- **celery**: Background task worker (internal only)
- **celery-beat**: Scheduled task scheduler (internal only)
- **redis**: Message broker (internal only)
- **flower**: Celery monitoring (internal only)

## Docker Compose Commands

### Basic Operations

```bash
# Start all services
docker-compose up -d

# Build and start services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View service status
docker-compose ps
```

### Service-Specific Operations

```bash
# View specific service logs
docker-compose logs -f api
docker-compose logs -f celery
docker-compose logs -f redis

# Restart specific service
docker-compose restart api

# Rebuild specific service
docker-compose up -d --build api
```

### Development Operations

```bash
# Start services in development mode
docker-compose up -d

# View real-time logs
docker-compose logs -f

# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: This will delete data)
docker-compose down -v
```

## API Endpoints

Once deployed, the following endpoints are available:

- **API Base**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **API Info**: http://localhost:8000/api/v1/info
- **Metrics**: http://localhost:8000/api/v1/metrics

## Development

### Local Development with Docker

```bash
# Start services in development mode
docker-compose up -d

# View API logs
docker-compose logs -f api

# View Celery logs
docker-compose logs -f celery
```

### Local Development without Docker

```bash
# Install uv if not already installed
pip install uv

# Install dependencies
uv sync

# Initialize database
uv run python -m pollinexus.cli init-db

# Start development server
uv run uvicorn pollinexus.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

### Environment Variables

The application uses the following environment variables (configured in docker-compose.yml):

```bash
ENVIRONMENT=development
DATABASE_URL=duckdb:///pollinexus.db
LOG_LEVEL=INFO
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### Data Directories

The following directories are mounted as volumes:

- `./uploads`: File uploads
- `./visualizations`: Generated visualizations
- `./results`: Analysis results
- `./logs`: Application logs
- `./data`: Database and data files

## Monitoring

### Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check API metrics
curl http://localhost:8000/api/v1/metrics
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f celery
docker-compose logs -f redis
```

## Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   
   # Stop conflicting service or change port in docker-compose.yml
   ```

2. **Permission issues**:
   ```bash
   # Create directories with proper permissions
   mkdir -p uploads visualizations results logs data
   chmod 755 uploads visualizations results logs data
   ```

3. **Database issues**:
   ```bash
   # Reinitialize database
   docker-compose exec api uv run python -m pollinexus.cli init-db
   ```

### Service Management

```bash
# Restart specific service
docker-compose restart api

# Rebuild specific service
docker-compose up -d --build api

# View service status
docker-compose ps
```

## Testing

### Run Tests

```bash
# Run tests in container
docker-compose exec api uv run python -m pytest test/

# Run tests locally
uv run python -m pytest test/
```

### API Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test API documentation
curl http://localhost:8000/docs
```

## Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: This will delete data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## Production Considerations

For production deployment, consider:

1. **Environment Variables**: Set appropriate production values
2. **Data Persistence**: Ensure data directories are properly backed up
3. **Monitoring**: Set up external monitoring for the API
4. **Security**: Configure proper firewall rules
5. **SSL**: Set up HTTPS with a reverse proxy if needed

---

**Note**: This is a simplified deployment guide focused on Docker Compose and `uv`. For more complex production deployments, consider using additional tools like Kubernetes or cloud-specific deployment services. 