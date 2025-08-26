# Pollinexus Documentation

Welcome to the Pollinexus documentation! This directory contains comprehensive documentation for the Pollinexus data science project focused on pollinator conservation.

## 📚 Documentation Index

### Core Documentation

- **[LICENSE.md](LICENSE.md)** - MIT License for the project
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Guidelines for contributing to the project
- **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)** - Community standards and behavior guidelines
- **[CHANGELOG.md](CHANGELOG.md)** - Project changelog and version history

### API Documentation

- **[API.md](API.md)** - Comprehensive API documentation with examples

#### API Overview

The Pollinexus API provides a complete RESTful interface for managing pollinator data, performing analysis, and creating visualizations. The API is built with FastAPI and includes comprehensive logging and monitoring.

**Key Features:**
- **Dataset Management**: Upload, validate, and manage pollinator datasets
- **Analysis Operations**: ML-based bee preference analysis and plant recommendations
- **Visualization**: Interactive charts and dashboards
- **Background Processing**: Asynchronous task processing with Celery
- **Monitoring**: Real-time job status and performance tracking

**Base URL:** `http://localhost:8000/api/v1`

**Interactive Documentation:** http://localhost:8000/docs

#### API Endpoints

**Dataset Management:**
- `POST /datasets/` - Upload and create dataset
- `GET /datasets/` - List datasets with pagination
- `GET /datasets/{id}` - Get dataset details
- `PUT /datasets/{id}` - Update dataset
- `DELETE /datasets/{id}` - Delete dataset
- `GET /datasets/{id}/info` - Get dataset statistics
- `POST /datasets/search` - Search datasets
- `GET /datasets/{id}/health` - Dataset health check

**Analysis Operations:**
- `POST /analysis/bee-preferences/` - Start bee preference analysis
- `POST /analysis/plant-recommendations/` - Start plant recommendations
- `POST /analysis/seasonal/` - Start seasonal analysis
- `POST /analysis/site-comparison/` - Start site comparison
- `GET /analysis/jobs/{id}` - Get analysis job
- `GET /analysis/jobs/` - List analysis jobs
- `GET /analysis/jobs/{id}/results` - Get analysis results
- `GET /analysis/jobs/{id}/status` - Get job status
- `DELETE /analysis/jobs/{id}` - Cancel analysis job
- `GET /analysis/stats` - Get analysis statistics

**Visualization Operations:**
- `POST /visualizations/bee-distribution/` - Create bee distribution plot
- `POST /visualizations/seasonal-patterns/` - Create seasonal patterns plot
- `POST /visualizations/site-comparison/` - Create site comparison plot
- `POST /visualizations/dashboard/` - Create interactive dashboard
- `POST /visualizations/batch/` - Create batch visualizations
- `GET /visualizations/{id}/status` - Get visualization status
- `GET /visualizations/{id}/download` - Download visualization
- `DELETE /visualizations/{id}` - Cancel visualization
- `GET /visualizations/available-types` - Get available visualization types

#### Quick API Examples

**Upload Dataset:**
```bash
curl -X POST "http://localhost:8000/api/v1/datasets/" \
  -F "name=Plants and Bees Dataset" \
  -F "description=Sample pollinator data" \
  -F "file=@plants_and_bees.csv"
```

**Start Analysis:**
```bash
curl -X POST "http://localhost:8000/api/v1/analysis/bee-preferences/" \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": 1, "target_column": "nonnative_bee", "model_type": "random_forest"}'
```

**Create Visualization:**
```bash
curl -X POST "http://localhost:8000/api/v1/visualizations/bee-distribution/?dataset_id=1"
```

For complete API documentation with all endpoints, request/response examples, and error handling, see **[API.md](API.md)**.

## 🚀 Getting Started

1. **Install the project:**
   ```bash
   pip install -e .
   ```

2. **Set up environment:**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Initialize database:**
   ```bash
   python -m pollinexus.cli init-db
   ```

4. **Run the API server:**
   ```bash
   uvicorn pollinexus.api.main:app --reload
   ```

5. **Access documentation:**
   - Interactive API docs: http://localhost:8000/docs
   - ReDoc documentation: http://localhost:8000/redoc

## 📖 Additional Resources

- **Main README**: [../README.md](../README.md) - Project overview and quick start
- **Development Plan**: [../todo/DEVELOPMENT_PLAN.md](../todo/DEVELOPMENT_PLAN.md) - Development roadmap
- **Immediate Tasks**: [../todo/IMMEDIATE_TASKS.md](../todo/IMMEDIATE_TASKS.md) - Current development tasks
- **Analysis Notebook**: [../todo/project.ipynb](../todo/project.ipynb) - Jupyter notebook with analysis examples

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Code style and standards
- Testing requirements
- Documentation updates
- Pull request process

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/pollinexus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/pollinexus/discussions)
- **Documentation**: This directory contains all project documentation

## 📄 License

This project is licensed under the MIT License - see [LICENSE.md](LICENSE.md) for details. 