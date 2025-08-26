# Pollinexus API Documentation

## Overview

The Pollinexus API provides comprehensive endpoints for managing pollinator data, performing analysis, and creating visualizations. The API is built with FastAPI and follows RESTful principles with comprehensive logging and monitoring.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, the API operates without authentication for development. Production deployments should implement proper authentication mechanisms.

## Response Format

All API responses follow a consistent JSON format:

```json
{
  "data": {...},
  "message": "Success",
  "status": "success"
}
```

Error responses include:

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "status": "error"
}
```

## Endpoints

### Dataset Management

#### Create Dataset
**POST** `/datasets/`

Upload and create a new dataset with validation.

**Parameters:**
- `name` (string, required): Dataset name
- `description` (string, optional): Dataset description
- `file` (file, required): Dataset file (CSV, Excel, Parquet)

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/datasets/" \
  -F "name=Plants and Bees Dataset" \
  -F "description=Sample pollinator data from environmental study" \
  -F "file=@plants_and_bees.csv"
```

**Response:**
```json
{
  "id": 1,
  "name": "Plants and Bees Dataset",
  "description": "Sample pollinator data from environmental study",
  "file_path": "uploads/1703123456_plants_and_bees.csv",
  "created_at": "2023-12-21T10:30:00Z",
  "updated_at": "2023-12-21T10:30:00Z"
}
```

#### List Datasets
**GET** `/datasets/`

Retrieve a list of datasets with pagination and search.

**Parameters:**
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Number of records to return (default: 10, max: 100)
- `search` (string, optional): Search term for dataset name or description

**Example:**
```bash
# Basic list
curl "http://localhost:8000/api/v1/datasets/"

# With pagination
curl "http://localhost:8000/api/v1/datasets/?skip=0&limit=20"

# With search
curl "http://localhost:8000/api/v1/datasets/?search=pollinator"
```

**Response:**
```json
{
  "datasets": [
    {
      "id": 1,
      "name": "Plants and Bees Dataset",
      "description": "Sample pollinator data",
      "file_path": "uploads/1703123456_plants_and_bees.csv",
      "created_at": "2023-12-21T10:30:00Z",
      "updated_at": "2023-12-21T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 10,
  "has_next": false,
  "has_prev": false
}
```

#### Get Dataset
**GET** `/datasets/{dataset_id}`

Retrieve a specific dataset by ID.

**Example:**
```bash
curl "http://localhost:8000/api/v1/datasets/1"
```

#### Update Dataset
**PUT** `/datasets/{dataset_id}`

Update dataset information.

**Example:**
```bash
curl -X PUT "http://localhost:8000/api/v1/datasets/1" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Dataset Name", "description": "Updated description"}'
```

#### Delete Dataset
**DELETE** `/datasets/{dataset_id}`

Delete a dataset and associated files.

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/datasets/1"
```

#### Get Dataset Info
**GET** `/datasets/{dataset_id}/info`

Get detailed dataset information and statistics.

**Example:**
```bash
curl "http://localhost:8000/api/v1/datasets/1/info"
```

**Response:**
```json
{
  "dataset": {
    "id": 1,
    "name": "Plants and Bees Dataset",
    "description": "Sample pollinator data",
    "file_path": "uploads/1703123456_plants_and_bees.csv",
    "created_at": "2023-12-21T10:30:00Z"
  },
  "statistics": {
    "total_records": 1000,
    "total_columns": 15,
    "memory_usage_mb": 2.5,
    "column_info": {
      "native_bee": {"dtype": "int64", "null_count": 0},
      "nonnative_bee": {"dtype": "int64", "null_count": 0}
    }
  },
  "file_info": {
    "file_path": "uploads/1703123456_plants_and_bees.csv",
    "file_size_mb": 2.5,
    "file_exists": true
  }
}
```

#### Search Datasets
**POST** `/datasets/search`

Search datasets by name, description, or content.

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/datasets/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "pollinator", "limit": 10, "offset": 0}'
```

#### Dataset Health Check
**GET** `/datasets/{dataset_id}/health`

Get dataset health and validation status.

**Example:**
```bash
curl "http://localhost:8000/api/v1/datasets/1/health"
```

**Response:**
```json
{
  "dataset_id": 1,
  "health_status": "healthy",
  "file_status": {
    "exists": true,
    "readable": true,
    "size_bytes": 2621440,
    "size_mb": 2.5
  },
  "validation_status": "valid",
  "validation_details": {
    "is_valid": true,
    "errors": [],
    "warnings": []
  },
  "last_checked": 1703123456
}
```

### Analysis Endpoints

#### Bee Preference Analysis
**POST** `/analysis/bee-preferences/`

Start ML-based bee preference analysis.

**Request Body:**
```json
{
  "dataset_id": 1,
  "target_column": "nonnative_bee",
  "model_type": "random_forest",
  "test_size": 0.2
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/analysis/bee-preferences/" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": 1,
    "target_column": "nonnative_bee",
    "model_type": "random_forest",
    "test_size": 0.2
  }'
```

**Response:**
```json
{
  "id": 1,
  "dataset_id": 1,
  "job_type": "bee_preferences",
  "status": "running",
  "parameters": {
    "target_column": "nonnative_bee",
    "model_type": "random_forest",
    "test_size": 0.2
  },
  "created_at": "2023-12-21T10:30:00Z",
  "celery_task_id": "abc123-def456"
}
```

#### Plant Recommendations
**POST** `/analysis/plant-recommendations/`

Start plant recommendation analysis.

**Request Body:**
```json
{
  "dataset_id": 1,
  "top_n": 10,
  "criteria": ["bee_attraction", "seasonal_availability"]
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/analysis/plant-recommendations/" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": 1,
    "top_n": 10,
    "criteria": ["bee_attraction", "seasonal_availability"]
  }'
```

#### Seasonal Analysis
**POST** `/analysis/seasonal/`

Start seasonal pattern analysis.

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/analysis/seasonal/?dataset_id=1" \
  -H "Content-Type: application/json" \
  -d '{"include_trends": true, "seasonal_periods": 12}'
```

#### Site Comparison
**POST** `/analysis/site-comparison/`

Start site comparison analysis.

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/analysis/site-comparison/?dataset_id=1" \
  -H "Content-Type: application/json" \
  -d '{"metrics": ["total_bees", "diversity_index"], "group_by": "site"}'
```

#### Get Analysis Job
**GET** `/analysis/jobs/{job_id}`

Retrieve analysis job details.

**Example:**
```bash
curl "http://localhost:8000/api/v1/analysis/jobs/1"
```

#### List Analysis Jobs
**GET** `/analysis/jobs/`

List analysis jobs with filtering.

**Parameters:**
- `dataset_id` (integer, optional): Filter by dataset ID
- `status` (string, optional): Filter by job status
- `skip` (integer, optional): Number of records to skip
- `limit` (integer, optional): Number of records to return

**Example:**
```bash
# List all jobs
curl "http://localhost:8000/api/v1/analysis/jobs/"

# Filter by status
curl "http://localhost:8000/api/v1/analysis/jobs/?status=completed"

# Filter by dataset
curl "http://localhost:8000/api/v1/analysis/jobs/?dataset_id=1"
```

#### Get Analysis Results
**GET** `/analysis/jobs/{job_id}/results`

Retrieve analysis results.

**Example:**
```bash
curl "http://localhost:8000/api/v1/analysis/jobs/1/results"
```

**Response:**
```json
{
  "job_id": 1,
  "job_type": "bee_preferences",
  "status": "completed",
  "results": {
    "model_performance": {
      "accuracy": 0.85,
      "precision": 0.82,
      "recall": 0.88,
      "f1_score": 0.85
    },
    "feature_importance": {
      "plant_species": 0.25,
      "season": 0.20,
      "site_location": 0.15
    },
    "predictions": [...]
  },
  "completed_at": "2023-12-21T10:35:00Z",
  "parameters": {
    "target_column": "nonnative_bee",
    "model_type": "random_forest",
    "test_size": 0.2
  }
}
```

#### Get Job Status
**GET** `/analysis/jobs/{job_id}/status`

Get detailed job status including Celery task status.

**Example:**
```bash
curl "http://localhost:8000/api/v1/analysis/jobs/1/status"
```

**Response:**
```json
{
  "job_id": 1,
  "job_type": "bee_preferences",
  "status": "running",
  "created_at": "2023-12-21T10:30:00Z",
  "started_at": "2023-12-21T10:30:05Z",
  "completed_at": null,
  "celery_task_id": "abc123-def456",
  "celery_status": {
    "status": "PENDING",
    "ready": false,
    "successful": false,
    "failed": false
  },
  "parameters": {
    "target_column": "nonnative_bee",
    "model_type": "random_forest",
    "test_size": 0.2
  }
}
```

#### Cancel Analysis Job
**DELETE** `/analysis/jobs/{job_id}`

Cancel a running analysis job.

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/analysis/jobs/1"
```

#### Analysis Statistics
**GET** `/analysis/stats`

Get analysis statistics and summary.

**Example:**
```bash
curl "http://localhost:8000/api/v1/analysis/stats"
```

### Visualization Endpoints

#### Bee Distribution Plot
**POST** `/visualizations/bee-distribution/`

Create bee species distribution visualization.

**Parameters:**
- `dataset_id` (integer, required): Dataset ID
- `parameters` (object, optional): Visualization parameters

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/visualizations/bee-distribution/?dataset_id=1" \
  -H "Content-Type: application/json" \
  -d '{"top_n": 20, "include_percentages": true}'
```

**Response:**
```json
{
  "id": 1703123456,
  "dataset_id": 1,
  "plot_type": "bee_distribution",
  "plot_data": {
    "task_id": "def456-ghi789"
  },
  "plot_config": {
    "top_n": 20,
    "include_percentages": true
  },
  "created_at": 1703123456
}
```

#### Seasonal Patterns Plot
**POST** `/visualizations/seasonal-patterns/`

Create seasonal patterns visualization.

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/visualizations/seasonal-patterns/?dataset_id=1" \
  -H "Content-Type: application/json" \
  -d '{"include_trends": true, "seasonal_periods": 12}'
```

#### Site Comparison Plot
**POST** `/visualizations/site-comparison/`

Create site comparison visualization.

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/visualizations/site-comparison/?dataset_id=1" \
  -H "Content-Type: application/json" \
  -d '{"metrics": ["total_bees", "diversity"], "group_by": "site"}'
```

#### Interactive Dashboard
**POST** `/visualizations/dashboard/`

Create comprehensive interactive dashboard.

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/visualizations/dashboard/?dataset_id=1" \
  -H "Content-Type: application/json" \
  -d '{"include_timeline": true, "include_metrics": true}'
```

#### Batch Visualization
**POST** `/visualizations/batch/`

Create multiple visualizations in batch.

**Request Body:**
```json
{
  "dataset_id": 1,
  "plot_types": ["bee_distribution", "seasonal_patterns", "site_comparison"],
  "parameters": {
    "top_n": 20,
    "include_trends": true
  }
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/visualizations/batch/" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": 1,
    "plot_types": ["bee_distribution", "seasonal_patterns", "site_comparison"],
    "parameters": {
      "top_n": 20,
      "include_trends": true
    }
  }'
```

**Response:**
```json
[
  {
    "id": 1703123456,
    "dataset_id": 1,
    "plot_type": "bee_distribution",
    "plot_data": {"task_id": "abc123-def456"},
    "plot_config": {"top_n": 20, "include_trends": true},
    "created_at": 1703123456
  },
  {
    "id": 1703123457,
    "dataset_id": 1,
    "plot_type": "seasonal_patterns",
    "plot_data": {"task_id": "def456-ghi789"},
    "plot_config": {"top_n": 20, "include_trends": true},
    "created_at": 1703123457
  }
]
```

#### Get Visualization Status
**GET** `/visualizations/{visualization_id}/status`

Get visualization task status.

**Parameters:**
- `visualization_id` (integer, required): Visualization ID
- `task_id` (string, required): Celery task ID

**Example:**
```bash
curl "http://localhost:8000/api/v1/visualizations/1703123456/status?task_id=abc123-def456"
```

**Response:**
```json
{
  "visualization_id": 1703123456,
  "task_id": "abc123-def456",
  "status": "SUCCESS",
  "ready": true,
  "successful": true,
  "failed": false,
  "info": {
    "plot_path": "visualizations/bee_distribution_1703123456.html",
    "plot_filename": "bee_distribution_1703123456.html",
    "plot_type": "bee_distribution"
  }
}
```

#### Download Visualization
**GET** `/visualizations/{visualization_id}/download`

Get visualization download information.

**Parameters:**
- `visualization_id` (integer, required): Visualization ID
- `task_id` (string, required): Celery task ID

**Example:**
```bash
curl "http://localhost:8000/api/v1/visualizations/1703123456/download?task_id=abc123-def456"
```

**Response:**
```json
{
  "visualization_id": 1703123456,
  "task_id": "abc123-def456",
  "plot_path": "visualizations/bee_distribution_1703123456.html",
  "plot_filename": "bee_distribution_1703123456.html",
  "plot_type": "bee_distribution",
  "file_size": 524288,
  "download_url": "/api/v1/visualizations/1703123456/file"
}
```

#### Cancel Visualization
**DELETE** `/visualizations/{visualization_id}`

Cancel a running visualization task.

**Parameters:**
- `visualization_id` (integer, required): Visualization ID
- `task_id` (string, required): Celery task ID

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/visualizations/1703123456?task_id=abc123-def456"
```

#### Available Visualization Types
**GET** `/visualizations/available-types`

Get list of available visualization types.

**Example:**
```bash
curl "http://localhost:8000/api/v1/visualizations/available-types"
```

**Response:**
```json
{
  "visualization_types": [
    {
      "type": "bee_distribution",
      "name": "Bee Species Distribution",
      "description": "Interactive bar chart showing bee species distribution",
      "parameters": {
        "top_n": "Number of top species to display (default: 20)"
      }
    },
    {
      "type": "seasonal_patterns",
      "name": "Seasonal Patterns",
      "description": "Multi-panel analysis of seasonal bee activity patterns",
      "parameters": {
        "include_trends": "Include trend lines (default: true)"
      }
    },
    {
      "type": "site_comparison",
      "name": "Site Comparison",
      "description": "Comparison of bee activity across different sites",
      "parameters": {
        "metrics": "Metrics to compare (default: ['total_bees', 'diversity'])"
      }
    },
    {
      "type": "interactive_dashboard",
      "name": "Interactive Dashboard",
      "description": "Comprehensive dashboard with multiple visualizations",
      "parameters": {
        "include_timeline": "Include timeline view (default: true)",
        "include_metrics": "Include summary metrics (default: true)"
      }
    }
  ],
  "total_types": 4
}
```

## Error Handling

The API uses standard HTTP status codes:

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

### Error Response Format

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "status": "error",
  "timestamp": "2023-12-21T10:30:00Z"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. Limits are configurable and will be enforced in production.

## Logging and Monitoring

All API endpoints include comprehensive logging:

- **Request Logging**: Every request logged with correlation IDs
- **Performance Monitoring**: Response time and resource usage tracking
- **Error Tracking**: Detailed error logging with context
- **Operation Tracking**: Start, progress, completion logging

## Development

### Running the API

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn pollinexus.api.main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation

Once the server is running, you can access:

- **Interactive API Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Testing

### Health Check

```bash
curl "http://localhost:8000/health"
```

### Example Workflow

1. **Upload Dataset:**
```bash
curl -X POST "http://localhost:8000/api/v1/datasets/" \
  -F "name=Plants and Bees Dataset" \
  -F "description=Sample pollinator data" \
  -F "file=@plants_and_bees.csv"
```

2. **Start Analysis:**
```bash
curl -X POST "http://localhost:8000/api/v1/analysis/bee-preferences/" \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": 1, "target_column": "nonnative_bee", "model_type": "random_forest"}'
```

3. **Check Job Status:**
```bash
curl "http://localhost:8000/api/v1/analysis/jobs/1/status"
```

4. **Get Results:**
```bash
curl "http://localhost:8000/api/v1/analysis/jobs/1/results"
```

5. **Create Visualization:**
```bash
curl -X POST "http://localhost:8000/api/v1/visualizations/bee-distribution/?dataset_id=1"
```

6. **Download Visualization:**
```bash
curl "http://localhost:8000/api/v1/visualizations/1703123456/download?task_id=abc123-def456"
```

## Production Considerations

- Implement proper authentication and authorization
- Configure rate limiting for production loads
- Set up monitoring and alerting
- Use HTTPS in production
- Configure proper CORS settings
- Implement request validation and sanitization
- Set up proper logging and error tracking
- Configure database connection pooling
- Implement caching strategies
- Set up backup and recovery procedures 