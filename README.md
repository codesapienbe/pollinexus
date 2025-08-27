# 🐝 Pollinexus - Data-Driven Pollinator Conservation API

A comprehensive API platform for environmental agencies to analyze pollinator data, generate insights, and support conservation efforts through machine learning and data science.

## 🚀 Current Status

**Sprint 3 Complete** ✅ - All core API endpoints implemented with comprehensive logging, monitoring, and security features.

### ✅ Completed Features

- **Core API Infrastructure**
  - FastAPI application with comprehensive middleware
  - Structured logging with OpenTelemetry compatibility
  - Error tracking and monitoring
  - Performance metrics collection
  - Health check endpoints

- **Data Management**
  - Dataset upload and validation
  - CSV file processing with security checks
  - Data cleaning and preprocessing
  - Database persistence with PostgreSQL
  - DuckDB integration for analytics

- **Analysis Engine**
  - Bee species preference analysis
  - Plant recommendation generation
  - Seasonal pattern analysis
  - Site comparison analytics
  - Machine learning model integration

- **Background Processing**
  - Celery task queue integration
  - Asynchronous job processing
  - Task status tracking
  - Result caching with Redis

- **User Management**
  - User registration and authentication
  - OTP-based verification system
  - Role-based access control
  - Session management

- **Visualization Services**
  - Interactive chart generation
  - Dashboard creation
  - Batch visualization processing
  - Multiple output formats

- **Security Features**
  - Input validation and sanitization
  - SQL injection prevention
  - XSS protection
  - File upload security
  - Rate limiting
  - CORS configuration

## 🎯 Next Steps: Sprint 4 - Testing & Quality Assurance

### Immediate Priorities

1. **Comprehensive Testing Suite** 🔄
   - Unit tests for all components
   - Integration tests for API endpoints
   - Security vulnerability testing
   - Performance and load testing
   - Database migration testing

2. **Production Deployment** 🚀
   - Docker containerization
   - Kubernetes deployment manifests
   - CI/CD pipeline setup
   - Monitoring and alerting
   - Backup and disaster recovery

3. **Documentation & Training** 📚
   - API documentation updates
   - User guides and tutorials
   - Developer onboarding materials
   - Deployment runbooks

## 🛠️ Quick Start

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+

### Development Setup

```bash
# Clone the repository
git clone https://github.com/your-username/pollinexus.git
cd pollinexus

# Install dependencies
pip install -e ".[dev]"

# Set up environment
cp env.example .env
# Edit .env with your configuration

# Initialize database
python -m pollinexus.cli init_db

# Start development server
uvicorn pollinexus.api.main:app --reload

# Start Celery worker (in new terminal)
celery -A pollinexus.tasks.celery_app worker --loglevel=info
```

### Production Deployment

```bash
# Deploy to production
./scripts/deploy.sh production

# Monitor deployment
docker-compose -f docker/production/docker-compose.yml logs -f

# Access services
# API: http://localhost
# Grafana: http://localhost:3000
# Prometheus: http://localhost:9090
# Kibana: http://localhost:5601
```

## 🚀 CI/CD/CT Pipeline

### Pipeline Validation

```bash
# Make validation script executable
chmod +x scripts/validate_pipeline.sh

# Run comprehensive pipeline validation
./scripts/validate_pipeline.sh

# Or run quick validation
python test/run_tests.py --type all --verbose
```

### Manual Pipeline Trigger

1. **Navigate to GitHub Actions**:
   - Go to your repository on GitHub
   - Click on the "Actions" tab
   - Select "CI/CD Pipeline" workflow

2. **Trigger Manual Run**:
   - Click "Run workflow" button
   - Select branch: `main` or `develop`
   - Choose environment: `staging` or `production`
   - Enable "Retrain models" if needed
   - Click "Run workflow"

### Pipeline Features

#### ✅ **Continuous Integration**
- **Security Scanning**: Trivy, Bandit, Safety
- **Code Quality**: Black, isort, Flake8, MyPy, Pylint
- **Testing**: Unit, integration, API, security, performance tests
- **Coverage**: Automated test coverage reporting

#### ✅ **Continuous Deployment**
- **Multi-environment**: Staging and production deployments
- **Docker**: Automated image building and pushing
- **Kubernetes**: Production-ready deployment manifests
- **Rollback**: Automated rollback capabilities

#### ✅ **Continuous Training**
- **Model Training**: Automated ML model retraining
- **Model Registry**: Version tracking and performance monitoring
- **Data Validation**: Automated data quality checks
- **Performance Monitoring**: Model drift detection

For detailed pipeline documentation, see: [CI/CD Guide](docs/CI_CD_GUIDE.md)

## 📊 API Endpoints

### Datasets

- `POST /api/v1/datasets/` - Upload dataset
- `GET /api/v1/datasets/` - List datasets
- `GET /api/v1/datasets/{id}` - Get dataset
- `DELETE /api/v1/datasets/{id}` - Delete dataset
- `GET /api/v1/datasets/{id}/info` - Dataset statistics
- `GET /api/v1/datasets/search` - Search datasets

### Analysis

- `POST /api/v1/analysis/bee-preferences/` - Start bee analysis
- `POST /api/v1/analysis/plant-recommendations/` - Generate recommendations
- `GET /api/v1/analysis/jobs/{id}` - Get job status
- `GET /api/v1/analysis/jobs/{id}/results` - Get results

### Visualizations

- `POST /api/v1/visualizations/bee-distribution/` - Create bee charts
- `POST /api/v1/visualizations/seasonal-patterns/` - Seasonal analysis
- `POST /api/v1/visualizations/dashboard/` - Generate dashboard
- `GET /api/v1/visualizations/{id}/download` - Download visualization

### User Management

- `POST /user/register` - Register user
- `POST /user/login` - Login
- `POST /user/verify-registration` - Verify account
- `GET /user/me` - Get user profile

## 🔧 Testing

### Run All Tests

```bash
# Run comprehensive test suite
python test/run_tests.py --type all

# Run specific test categories
python test/run_tests.py --type security
python test/run_tests.py --type performance
python test/run_tests.py --type api
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **API Tests**: Endpoint functionality testing
- **Security Tests**: Vulnerability and security testing
- **Performance Tests**: Load and stress testing
- **Database Tests**: Data persistence testing

## 📈 Monitoring & Observability

### Metrics Collection

- **Prometheus**: System and application metrics
- **Grafana**: Visualization and dashboards
- **Elasticsearch**: Log aggregation and search
- **Kibana**: Log visualization and analysis

### Health Checks

- Application health: `/health`
- Database connectivity
- Redis connectivity
- Celery worker status
- External service dependencies

### Logging

- Structured JSON logging
- Request/response correlation
- Error tracking and alerting
- Performance monitoring
- Security event logging

## 🔒 Security Features

### Input Validation

- SQL injection prevention
- XSS protection
- File upload security
- Path traversal prevention
- Command injection protection

### Authentication & Authorization

- JWT token-based authentication
- OTP verification system
- Role-based access control
- Session management
- Rate limiting

### Data Protection

- Sensitive data encryption
- Secure file handling
- Audit logging
- Backup encryption
- Network security

## 🚀 Deployment Architecture

### Production Stack

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │   Load Balancer │    │   CDN/Edge      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Pollinexus API │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Redis       │    │   Elasticsearch │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Celery Workers │
                    └─────────────────┘
```

### Scalability Features

- Horizontal scaling with load balancers
- Database connection pooling
- Redis clustering for high availability
- Celery worker auto-scaling
- Container orchestration with Kubernetes

## 📚 Documentation

### API Documentation

- Interactive docs: `/docs` (Swagger UI)
- ReDoc documentation: `/redoc`
- OpenAPI schema: `/openapi.json`

### User Guides

- [Getting Started Guide](docs/GETTING_STARTED.md)
- [API Reference](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

### Developer Resources

- [Development Setup](docs/DEVELOPMENT.md)
- [Contributing Guidelines](docs/CONTRIBUTING.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Testing Guide](docs/TESTING.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](docs/CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Quality

- Type hints required
- Comprehensive test coverage
- Security review for all changes
- Performance testing for new features
- Documentation updates

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Environmental agencies for domain expertise
- Open source community for tools and libraries
- Research institutions for pollinator data
- Conservation organizations for guidance

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-username/pollinexus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/pollinexus/discussions)
- **Email**: <contact@pollinexus.org>

---

**Pollinexus** - Empowering environmental conservation through data-driven insights 🐝🌱
