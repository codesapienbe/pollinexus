# 🐝 Pollinexus - Data-Driven Pollinator Conservation Platform

A comprehensive data science platform for environmental agencies to analyze pollinator data, generate insights, and support conservation efforts through machine learning and advanced analytics.

## 🎯 Overview

Pollinexus transforms raw pollinator observation data into actionable conservation insights. The platform leverages machine learning to identify bee species preferences, predict optimal plant combinations, and analyze seasonal patterns across different habitats.

**Key Capabilities:**

- **Species Preference Analysis**: ML-driven identification of bee-plant relationships
- **Habitat Optimization**: Data-driven recommendations for pollinator-friendly environments  
- **Seasonal Pattern Recognition**: Time-series analysis of pollinator activity
- **Predictive Modeling**: Forecast pollinator presence based on environmental factors
- **Interactive Visualizations**: Dynamic dashboards for data exploration

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker (optional, for containerized deployment)
- Redis (auto-installed on local runs)

### Local Development

```bash
# Build and run locally
make build-local
make run-local

# Or use the quick start
make run
```

### Docker Deployment

```bash
# Build and run with Docker
make build-docker  
make run-docker
```

### Remote VM Deployment

```bash
# Deploy to remote VM (requires Vagrant)
make build-remote
make run-remote
```

## 🔬 Core Workflows

### Data Analysis Pipeline

```bash
# Upload and process dataset
curl -X POST "http://localhost:8000/api/v1/datasets/" \
  -F "file=@dataset/plants_and_bees.csv"

# Run bee preference analysis
curl -X POST "http://localhost:8000/api/v1/analysis/bee-preferences/" \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": 1, "analysis_type": "species_preference"}'

# Generate visualizations
curl -X POST "http://localhost:8000/api/v1/visualizations/bee-distribution/" \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": 1, "chart_type": "species_distribution"}'
```

### Model Training

```bash
# Train ML models locally
make train-local

# Train with Docker
make train-docker

# Train on remote VM
make train-remote
```

### Quality Assurance

```bash
# Run comprehensive verification (tests, linting, formatting)
make verify-local

# Verify remote deployment
make verify-remote
```

## 📊 Data Science Features

### Machine Learning Models

- **Species Classification**: Identify bee species from observation data
- **Preference Prediction**: Predict plant preferences for different bee species
- **Habitat Suitability**: Assess environmental factors for pollinator success
- **Seasonal Forecasting**: Predict pollinator activity patterns

### Analytics Capabilities

- **Statistical Analysis**: Correlation studies, significance testing
- **Geospatial Analysis**: Location-based pattern recognition
- **Time Series Analysis**: Seasonal and trend analysis
- **Clustering**: Identify similar habitats and species groups

### Visualization Engine

- **Interactive Charts**: Dynamic species distribution maps
- **Dashboard Generation**: Automated report creation
- **Export Capabilities**: Multiple format support (PNG, PDF, SVG)
- **Real-time Updates**: Live data visualization

## 🏗️ Architecture

The platform follows a microservices architecture with:

- **FastAPI Backend**: High-performance API with async processing
- **Celery Task Queue**: Background job processing for heavy computations
- **PostgreSQL**: Primary data storage with advanced querying
- **DuckDB**: Analytics engine for complex data operations
- **Redis**: Caching and session management
- **ML Pipeline**: Automated model training and deployment

## 📚 Documentation

- **[API Documentation](docs/API.md)** - Complete endpoint reference
- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design and components
- **[Contributing Guidelines](docs/CONTRIBUTING.md)** - Development workflow
- **[API Groups](docs/api-groups/)** - Organized endpoint documentation

## 🔧 Available Commands

```bash
# Build commands
make build          # Build with default environment
make build-local    # Build locally
make build-docker   # Build with Docker
make build-remote   # Build on remote VM

# Run commands  
make run            # Run with default environment
make run-local      # Run locally
make run-docker     # Run with Docker
make run-remote     # Run on remote VM

# Training commands
make train          # Train with default environment
make train-local    # Train locally
make train-docker   # Train with Docker
make train-remote   # Train on remote VM

# Utility commands
make clean-local    # Clean local artifacts
make clean-docker   # Clean Docker artifacts
make verify-local   # Run all tests and checks
make verify-remote  # Verify remote deployment
```

## 🤝 Contributing

See [Contributing Guidelines](docs/CONTRIBUTING.md) for development workflow and code standards.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Pollinexus** - Empowering environmental conservation through data-driven insights 🐝🌱
