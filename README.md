# 🐝 Pollinexus

**Data-Driven Pollinator Conservation for Environmental Agencies**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](docs/LICENSE.md)
[![Contributing](https://img.shields.io/badge/Contributing-Welcome-orange.svg)](docs/CONTRIBUTING.md)

## 📖 Overview

Pollinexus is a comprehensive data science project designed to support environmental agencies in creating optimal habitats for pollinator bees. By analyzing the relationship between native/non-native plants and bee species, this project provides evidence-based recommendations for pollinator conservation efforts.

### 🎯 Mission

To empower environmental agencies with data-driven insights for establishing pollinator-friendly areas that maximize native bee populations while supporting ecosystem health.

## 🌟 Key Features

- **Data Analysis Pipeline**: Clean, process, and analyze plant-bee interaction data
- **Machine Learning Models**: Identify plant preferences for native vs non-native bee species
- **Visualization Tools**: Interactive charts showing bee and plant species distributions
- **Recommendation Engine**: Top plant species recommendations for native bee support
- **Environmental Impact Assessment**: Evidence-based conservation strategies

## 📊 Dataset

The project analyzes the `plants_and_bees.csv` dataset containing:

| Column | Description |
|--------|-------------|
| `sample_id` | Unique sample identifier |
| `bees_num` | Total bee individuals in sample |
| `date` | Sample collection date |
| `season` | Early or late season sampling |
| `site` | Collection site identifier |
| `native_or_non` | Native or non-native plot |
| `sampling` | Sampling method used |
| `plant_species` | Plant species sampled (None = air sample) |
| `time` | Sample collection time |
| `bee_species` | Bee species identified |
| `sex` | Bee gender |
| `specialized_on` | Preferred plant genus |
| `parasitic` | Parasitic behavior (0=no, 1=yes) |
| `nesting` | Nesting method |
| `status` | Bee species status |
| `nonnative_bee` | Native status (0=native, 1=non-native) |

**Source**: [DataDryad Dataset](https://datadryad.org/stash/dataset/doi%253A10.5061%252Fdryad.pzgmsbcj8) (modified for educational purposes)

## 🚀 Getting Started

### Prerequisites

- Python 3.12 or higher
- Jupyter Notebook or JupyterLab
- Required Python packages (see `pyproject.toml`)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/codesapienbe/pollinexus.git
   cd pollinexus
   ```

2. **Install dependencies**

   ```bash
   pip install -e .
   ```

3. **Set up environment**

   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize the database**

   ```bash
   python -m pollinexus.cli init-db
   ```

5. **Run the API server**

   ```bash
   uvicorn pollinexus.api.main:app --reload
   ```

6. **Access the API**
   - Interactive docs: http://localhost:8000/docs
   - API base URL: http://localhost:8000/api/v1

### API Usage Examples

#### Dataset Management

**Upload a dataset:**
```bash
curl -X POST "http://localhost:8000/api/v1/datasets/" \
  -F "name=Plants and Bees Dataset" \
  -F "description=Sample pollinator data from environmental study" \
  -F "file=@plants_and_bees.csv"
```

**List datasets:**
```bash
curl "http://localhost:8000/api/v1/datasets/?skip=0&limit=10"
```

**Get dataset info:**
```bash
curl "http://localhost:8000/api/v1/datasets/1/info"
```

#### Analysis Operations

**Start bee preference analysis:**
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

**Check analysis job status:**
```bash
curl "http://localhost:8000/api/v1/analysis/jobs/1/status"
```

**Get analysis results:**
```bash
curl "http://localhost:8000/api/v1/analysis/jobs/1/results"
```

#### Visualization Operations

**Create bee distribution plot:**
```bash
curl -X POST "http://localhost:8000/api/v1/visualizations/bee-distribution/?dataset_id=1" \
  -H "Content-Type: application/json" \
  -d '{"top_n": 20, "include_percentages": true}'
```

**Create batch visualizations:**
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

**Download visualization:**
```bash
curl "http://localhost:8000/api/v1/visualizations/1703123456/download?task_id=abc123-def456"
```

#### Complete Workflow Example

```bash
# 1. Upload dataset
curl -X POST "http://localhost:8000/api/v1/datasets/" \
  -F "name=Plants and Bees Dataset" \
  -F "description=Sample pollinator data" \
  -F "file=@plants_and_bees.csv"

# 2. Start analysis
curl -X POST "http://localhost:8000/api/v1/analysis/bee-preferences/" \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": 1, "target_column": "nonnative_bee", "model_type": "random_forest"}'

# 3. Check status
curl "http://localhost:8000/api/v1/analysis/jobs/1/status"

# 4. Get results
curl "http://localhost:8000/api/v1/analysis/jobs/1/results"

# 5. Create visualization
curl -X POST "http://localhost:8000/api/v1/visualizations/bee-distribution/?dataset_id=1"

# 6. Download visualization
curl "http://localhost:8000/api/v1/visualizations/1703123456/download?task_id=abc123-def456"
```

### Jupyter Notebook Analysis

3. **Launch Jupyter**

   ```bash
   jupyter notebook
   ```

4. **Open the analysis notebook**
   - Navigate to `todo/project.ipynb`
   - Run all cells to reproduce the analysis

## 📈 Project Structure

```
pollinexus/
├── README.md                 # This file
├── pyproject.toml           # Project configuration
├── env.example              # Environment variables template
├── assets/                  # Static assets (images, etc.)
├── docs/                    # Documentation
│   ├── LICENSE.md          # Project license
│   ├── CONTRIBUTING.md     # Contribution guidelines
│   ├── CODE_OF_CONDUCT.md  # Community standards
│   ├── API.md              # API documentation
│   ├── CHANGELOG.md        # Project changelog
│   └── README.md           # Documentation index
├── src/                     # Source code
│   └── pollinexus/         # Main package
│       ├── __init__.py     # Package initialization
│       ├── cli.py          # Command-line interface
│       ├── api/            # FastAPI application
│       │   ├── main.py     # Main API application
│       │   ├── models/     # Request/response models
│       │   └── routes/     # API route handlers
│       ├── core/           # Core functionality
│       │   ├── config.py   # Configuration management
│       │   ├── database.py # Database connection
│       │   ├── logging.py  # Logging configuration
│       │   ├── metrics.py  # Performance monitoring
│       │   └── error_tracking.py # Error handling
│       ├── models/         # Database models
│       ├── services/       # Business logic services
│       │   ├── data_service.py      # Data processing
│       │   ├── database_service.py  # Database operations
│       │   └── duckdb_service.py    # DuckDB operations
│       ├── tasks/          # Celery background tasks
│       │   ├── celery_app.py        # Celery configuration
│       │   ├── analysis.py          # Analysis tasks
│       │   ├── visualization.py     # Visualization tasks
│       │   └── data_processing.py   # Data processing tasks
│       └── utils/          # Utility functions
├── test/                    # Test suite
└── todo/                    # Analysis files
    ├── project.ipynb       # Main analysis notebook
    ├── plants_and_bees.csv # Dataset
    ├── DEVELOPMENT_PLAN.md # Development roadmap
    └── IMMEDIATE_TASKS.md  # Current tasks
```

## 🔬 Analysis Components

### 1. Data Management

- **Dataset Upload & Validation**: Multi-format support (CSV, Excel, Parquet)
- **Data Cleaning**: Automated cleaning and preprocessing
- **Data Validation**: Comprehensive validation with error reporting
- **Dataset Health Monitoring**: Real-time health checks and status monitoring

### 2. Machine Learning Analysis

- **Bee Preference Analysis**: ML models to identify plant preferences
- **Plant Recommendations**: Intelligent recommendation system
- **Seasonal Analysis**: Pattern analysis and trend identification
- **Site Comparison**: Cross-site analysis and ranking
- **Feature Importance**: Automated feature importance analysis

### 3. Visualization

- **Bee Distribution Plots**: Interactive species distribution charts
- **Seasonal Patterns**: Multi-panel seasonal analysis
- **Site Comparison**: Cross-site comparison visualizations
- **Interactive Dashboards**: Comprehensive data exploration tools
- **Batch Visualization**: Multiple plot generation

### 4. API & Services

- **RESTful API**: Complete REST API with comprehensive endpoints
- **Background Processing**: Celery-based asynchronous task processing
- **Real-time Monitoring**: Job status tracking and progress monitoring
- **File Management**: Automated file handling and cleanup
- **Comprehensive Logging**: OpenTelemetry-friendly logging and monitoring

### 5. Recommendations

- **Plant Recommendations**: Top plant species for native bee support
- **Conservation Strategies**: Evidence-based conservation recommendations
- **Implementation Guidelines**: Practical implementation guidance
- **Environmental Impact Assessment**: Impact analysis and reporting

## 🤝 Contributing

We welcome contributions from researchers, environmental scientists, and data enthusiasts! Please see our [Contributing Guidelines](docs/CONTRIBUTING.md) for details.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Code of Conduct

This project adheres to a [Code of Conduct](docs/CODE_OF_CONDUCT.md) to ensure a welcoming and inclusive environment for all contributors.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](docs/LICENSE.md) file for details.

## 🙏 Acknowledgments

- **Data Source**: Original dataset from DataDryad
- **Environmental Agencies**: For their commitment to pollinator conservation
- **Research Community**: For advancing pollinator science

## 📞 Contact

- **Project Maintainer**: [Your Name](mailto:your.email@example.com)
- **Issues**: [GitHub Issues](https://github.com/your-username/pollinexus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/pollinexus/discussions)

## 🔗 Related Projects

- [Bee Conservation Network](https://example.com)
- [Native Plant Database](https://example.com)
- [Pollinator Monitoring Initiative](https://example.com)

---

**Made with ❤️ for pollinator conservation**
