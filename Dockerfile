# Multi-stage Docker build for Pollinexus API
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY README.md ./

# Install Python dependencies with uv
RUN uv sync --frozen

# Copy application code
COPY src/ ./src/
COPY docs/ ./docs/

# Create necessary directories
RUN mkdir -p uploads visualizations results logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Default command
CMD ["uv", "run", "uvicorn", "pollinexus.api.main:app", "--host", "0.0.0.0", "--port", "8000"]


# Development stage
FROM base as development

# Copy test files
COPY test/ ./test/

# Set development environment
ENV ENVIRONMENT=development \
    LOG_LEVEL=DEBUG

# Development command
CMD ["uv", "run", "uvicorn", "pollinexus.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# Production stage
FROM base as production

# Set production environment
ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO

# Production optimizations
RUN pip install gunicorn

# Copy production configuration
COPY docker/production/gunicorn.conf.py ./

# Production command
CMD ["gunicorn", "pollinexus.api.main:app", "-c", "gunicorn.conf.py"] 