# 🚀 CI/CD/CT Pipeline Guide - Pollinexus

This guide covers the comprehensive Continuous Integration, Continuous Deployment, and Continuous Training (CI/CD/CT) pipeline for the Pollinexus API.

## 📋 Table of Contents

- [Overview](#overview)
- [Pipeline Architecture](#pipeline-architecture)
- [Setup Instructions](#setup-instructions)
- [Workflow Triggers](#workflow-triggers)
- [Security & Quality Gates](#security--quality-gates)
- [Model Training Pipeline](#model-training-pipeline)
- [Deployment Strategies](#deployment-strategies)
- [Monitoring & Observability](#monitoring--observability)
- [Pipeline Validation](#pipeline-validation)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## 🎯 Overview

The Pollinexus CI/CD/CT pipeline provides:

- **Automated Testing**: Unit, integration, security, and performance tests
- **Security Scanning**: Vulnerability detection and code quality checks
- **Model Training**: Automated ML model retraining and validation
- **Deployment**: Multi-environment deployment with rollback capabilities
- **Monitoring**: Comprehensive observability and alerting

## 🏗️ Pipeline Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Code Push     │    │   Pull Request  │    │   Scheduled     │
│                 │    │                 │    │   Training      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  GitHub Actions │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Security Scan  │    │   Code Quality  │    │   Test Suite    │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Build Images  │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Model Training  │    │  Deploy Staging │    │ Performance Test│
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Deploy Production│
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Monitoring    │
                    └─────────────────┘
```

## ⚙️ Setup Instructions

### 1. GitHub Repository Setup

```bash
# Clone the repository
git clone https://github.com/your-username/pollinexus.git
cd pollinexus

# Create and switch to develop branch
git checkout -b develop
git push -u origin develop
```

### 2. GitHub Secrets Configuration

Configure the following secrets in your GitHub repository:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://user:password@host:port/database

# API Configuration
API_SECRET_KEY=your-super-secret-key-here
GRAFANA_PASSWORD=your-grafana-password

# Container Registry
GHCR_TOKEN=your-github-container-registry-token

# Deployment Environments
STAGING_KUBECONFIG=base64-encoded-kubeconfig
PRODUCTION_KUBECONFIG=base64-encoded-kubeconfig

# Monitoring
SLACK_WEBHOOK_URL=your-slack-webhook-url
EMAIL_NOTIFICATIONS=your-email-config
```

### 3. Kubernetes Cluster Setup

```bash
# Create namespace
kubectl create namespace pollinexus

# Apply RBAC
kubectl apply -f k8s/rbac/

# Apply secrets
kubectl apply -f k8s/secrets/

# Apply storage classes
kubectl apply -f k8s/storage/
```

### 4. Monitoring Stack Setup

```bash
# Install Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring

# Install Grafana
helm install grafana grafana/grafana -n monitoring

# Install Elasticsearch
helm install elasticsearch elastic/elasticsearch -n monitoring

# Install Kibana
helm install kibana elastic/kibana -n monitoring
```

## 🔄 Workflow Triggers

### Automatic Triggers

1. **Push to main/develop**: Full CI/CD pipeline
2. **Pull Request**: Security scan, code quality, tests
3. **Weekly Schedule**: Model retraining (Sundays at 2 AM)

### Manual Triggers

```bash
# Deploy to staging
gh workflow run ci-cd.yml -f environment=staging

# Deploy to production
gh workflow run ci-cd.yml -f environment=production

# Retrain models
gh workflow run ci-cd.yml -f retrain_models=true
```

## 🔒 Security & Quality Gates

### Security Scanning

- **Trivy**: Container vulnerability scanning
- **Bandit**: Python security linting
- **Safety**: Dependency vulnerability check
- **CodeQL**: Static analysis security testing

### Code Quality

- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting
- **MyPy**: Type checking
- **Pylint**: Code analysis

### Quality Gates

```yaml
# Minimum requirements
test_coverage: 80%
security_score: A
performance_threshold: 2.0s
model_accuracy: 0.8
```

## 🤖 Model Training Pipeline

### Training Workflow

1. **Data Collection**: Download latest datasets
2. **Feature Engineering**: Prepare ML features
3. **Model Training**: Train multiple algorithms
4. **Validation**: Cross-validation and testing
5. **Performance Comparison**: Compare with current model
6. **Registry Update**: Update model registry
7. **Auto-Deployment**: Deploy if performance improves

### Training Configuration

```yaml
# models/training_config.yaml
training:
  algorithms:
    - random_forest
    - gradient_boosting
    - xgboost
  
  hyperparameter_optimization:
    trials: 50
    timeout: 3600
  
  validation:
    cross_validation_folds: 5
    test_size: 0.2
  
  deployment:
    auto_deploy: true
    improvement_threshold: 0.02
    performance_threshold: 0.8
```

### Model Registry Management

```bash
# Check model status
python scripts/update_model_registry.py --action list

# Deploy specific model
python scripts/update_model_registry.py --action deploy --version 20231201_120000

# Compare models
python scripts/update_model_registry.py --action compare --version 20231201_120000

# Cleanup old models
python scripts/update_model_registry.py --action cleanup --keep-versions 5
```

## 🚀 Deployment Strategies

### Staging Deployment

```bash
# Deploy to staging
kubectl apply -f k8s/staging/

# Run smoke tests
kubectl exec -it pollinexus-api -- curl -f http://localhost:8000/health

# Check logs
kubectl logs -f deployment/pollinexus-api
```

### Production Deployment

```bash
# Blue-Green Deployment
kubectl apply -f k8s/production/blue/
kubectl apply -f k8s/production/green/

# Switch traffic
kubectl patch ingress pollinexus-ingress -p '{"spec":{"rules":[{"host":"pollinexus.com","http":{"paths":[{"path":"/","backend":{"service":{"name":"pollinexus-api-service-green"}}}]}}]}}'

# Rollback if needed
kubectl rollout undo deployment/pollinexus-api
```

### Canary Deployment

```yaml
# k8s/production/canary.yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: pollinexus-api
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pollinexus-api
  progressDeadlineSeconds: 600
  service:
    port: 80
    targetPort: 8000
  analysis:
    interval: 30s
    threshold: 10
    maxWeight: 50
    stepWeight: 10
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
    - name: request-duration
      thresholdRange:
        max: 500
```

## 📊 Monitoring & Observability

### Metrics Collection

- **Application Metrics**: Request rate, response time, error rate
- **Business Metrics**: Dataset uploads, analysis jobs, user activity
- **ML Metrics**: Model accuracy, training time, prediction latency
- **Infrastructure Metrics**: CPU, memory, disk, network

### Alerting Rules

```yaml
# monitoring/alerts.yaml
groups:
- name: pollinexus
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: High error rate detected
      
  - alert: ModelAccuracyLow
    expr: pollinexus_model_accuracy < 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: Model accuracy below threshold
      
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: High response time detected
```

### Dashboard Configuration

```json
{
  "dashboard": {
    "title": "Pollinexus API Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Model Performance",
        "type": "stat",
        "targets": [
          {
            "expr": "pollinexus_model_accuracy",
            "legendFormat": "Accuracy"
          }
        ]
      }
    ]
  }
}
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Build Failures

```bash
# Check build logs
gh run list --limit 10
gh run view <run-id> --log

# Common fixes
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2. Test Failures

```bash
# Run tests locally
python test/run_tests.py --type unit --verbose

# Check test environment
export DATABASE_URL="sqlite:///test.db"
export CELERY_BROKER_URL="memory://"
python -m pytest test/ -v
```

#### 3. Deployment Issues

```bash
# Check pod status
kubectl get pods -n pollinexus

# Check pod logs
kubectl logs -f deployment/pollinexus-api

# Check events
kubectl get events -n pollinexus --sort-by='.lastTimestamp'

# Check ingress
kubectl describe ingress pollinexus-ingress
```

#### 4. Model Training Issues

```bash
# Check training logs
python scripts/train_models.py --verbose

# Validate data
python scripts/validate_data.py

# Check model registry
python scripts/update_model_registry.py --action report
```

### Debug Commands

```bash
# Debug Kubernetes deployment
kubectl describe deployment pollinexus-api
kubectl get pods -o wide
kubectl exec -it <pod-name> -- /bin/bash

# Debug application
kubectl port-forward svc/pollinexus-api-service 8000:80
curl -v http://localhost:8000/health

# Debug database
kubectl exec -it <postgres-pod> -- psql -U pollinexus -d pollinexus
```

## 🔍 Pipeline Validation

### Manual Pipeline Trigger

To validate the CI/CD/CT pipeline manually:

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

3. **Monitor Execution**:
   - Watch each job execute in real-time
   - Check for any failures or warnings
   - Review logs for detailed information

### Pipeline Validation Checklist

#### ✅ Pre-Validation
- [ ] GitHub secrets are configured
- [ ] Repository has proper permissions
- [ ] Docker registry access is set up
- [ ] Kubernetes cluster is accessible

#### ✅ Security & Quality Gates
- [ ] Trivy vulnerability scan passes
- [ ] Bandit security scan passes
- [ ] Safety dependency check passes
- [ ] Code formatting (Black, isort) passes
- [ ] Linting (Flake8, MyPy, Pylint) passes

#### ✅ Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] API tests pass
- [ ] Security tests pass
- [ ] Performance tests pass
- [ ] Test coverage meets threshold

#### ✅ Model Training
- [ ] Data validation passes
- [ ] Model training completes successfully
- [ ] Model performance metrics are acceptable
- [ ] Model registry is updated
- [ ] Model versioning works correctly

#### ✅ Deployment
- [ ] Docker images build successfully
- [ ] Images are pushed to registry
- [ ] Staging deployment succeeds
- [ ] Health checks pass
- [ ] Production deployment succeeds (if applicable)

### Local Pipeline Testing

Test pipeline components locally before pushing:

```bash
# Security scanning
trivy fs .
bandit -r src/
safety check

# Code quality
black --check src/
isort --check-only src/
flake8 src/
mypy src/
pylint src/

# Testing
python -m pytest test/ -v --cov=pollinexus

# Model training
python scripts/train_models.py --dry-run

# Docker build
docker build -t pollinexus:test .
```

### Pipeline Health Monitoring

Monitor pipeline health metrics:

```bash
# Check pipeline success rate
gh run list --limit 10 --json status,conclusion

# Check recent failures
gh run list --limit 10 --json status,conclusion | jq '.[] | select(.conclusion == "failure")'

# Check pipeline duration
gh run list --limit 10 --json status,conclusion,duration
```

### Common Validation Issues

#### 1. Secret Configuration
```bash
# Verify secrets are set
gh secret list

# Check if secrets are accessible
echo ${{ secrets.DATABASE_URL }}
```

#### 2. Docker Registry Access
```bash
# Test registry login
docker login ghcr.io -u $GITHUB_USERNAME -p $GITHUB_TOKEN

# Test image push
docker tag pollinexus:latest ghcr.io/username/pollinexus:test
docker push ghcr.io/username/pollinexus:test
```

#### 3. Kubernetes Access
```bash
# Test cluster access
kubectl cluster-info
kubectl get nodes

# Test namespace access
kubectl get pods -n pollinexus
```

### Pipeline Performance Metrics

Track these metrics for pipeline optimization:

- **Build Time**: Target < 10 minutes
- **Test Execution**: Target < 5 minutes
- **Deployment Time**: Target < 3 minutes
- **Success Rate**: Target > 95%
- **Security Scan Time**: Target < 2 minutes

### Validation Commands

```bash
# Complete pipeline validation
./scripts/validate_pipeline.sh

# Quick validation
./scripts/quick_validation.sh

# Security validation
./scripts/security_validation.sh
```

## 📚 Best Practices

### Code Quality

1. **Write Tests First**: TDD approach for new features
2. **Type Hints**: Use type hints for all functions
3. **Documentation**: Comprehensive docstrings and comments
4. **Code Review**: Require reviews for all changes
5. **Small Commits**: Atomic commits with clear messages

### Security

1. **Secret Management**: Use Kubernetes secrets, never commit secrets
2. **Image Scanning**: Scan all container images
3. **Network Policies**: Restrict pod-to-pod communication
4. **RBAC**: Principle of least privilege
5. **Regular Updates**: Keep dependencies updated

### Performance

1. **Resource Limits**: Set appropriate CPU/memory limits
2. **Horizontal Scaling**: Use HPA for automatic scaling
3. **Caching**: Implement Redis caching
4. **Database Optimization**: Use connection pooling
5. **Monitoring**: Monitor performance metrics

### ML Operations

1. **Model Versioning**: Track all model versions
2. **A/B Testing**: Test new models before deployment
3. **Data Validation**: Validate input data
4. **Performance Tracking**: Monitor model drift
5. **Automated Retraining**: Schedule regular retraining

### Deployment

1. **Blue-Green Deployment**: Zero-downtime deployments
2. **Rollback Strategy**: Quick rollback capabilities
3. **Health Checks**: Comprehensive health monitoring
4. **Backup Strategy**: Regular data backups
5. **Disaster Recovery**: Plan for failure scenarios

## 📞 Support

For issues with the CI/CD pipeline:

1. **Check Logs**: Review GitHub Actions logs
2. **Documentation**: Refer to this guide
3. **Issues**: Create GitHub issue with detailed information
4. **Slack**: Join our development Slack channel
5. **Email**: Contact the DevOps team

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Maintainer**: DevOps Team
