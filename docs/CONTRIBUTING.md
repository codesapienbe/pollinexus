# Contributing to Pollinexus

Thank you for your interest in contributing to Pollinexus! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

We welcome contributions from:
- **Environmental Scientists**: Domain expertise and research insights
- **Data Scientists**: Analysis improvements and model enhancements
- **Software Developers**: Code quality and feature development
- **Conservationists**: Real-world application and validation
- **Students**: Learning and research contributions

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## 📜 Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

## 🚀 Getting Started

### Prerequisites

- Python 3.12 or higher
- Git
- Jupyter Notebook or JupyterLab
- Basic understanding of data science and environmental science

### Setup Development Environment

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/pollinexus.git
   cd pollinexus
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## 🔄 Development Workflow

### 1. Issue Creation

Before starting work, create or find an issue that describes the problem or feature:

- **Bug reports**: Include steps to reproduce, expected vs actual behavior
- **Feature requests**: Describe the use case and expected benefits
- **Enhancements**: Explain the improvement and its impact

### 2. Branch Strategy

- **Main branch**: `main` - stable, production-ready code
- **Development branch**: `develop` - integration branch for features
- **Feature branches**: `feature/description` - new features
- **Bug fix branches**: `fix/description` - bug fixes
- **Hotfix branches**: `hotfix/description` - urgent fixes

### 3. Branch Naming Convention

```
type/description
```

Examples:
- `feature/ml-model-enhancement`
- `fix/data-cleaning-bug`
- `docs/api-documentation`
- `test/coverage-improvement`

## 📝 Code Standards

### Python Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use type hints for function parameters and return values
- Maximum line length: 88 characters (Black formatter)
- Use meaningful variable and function names

### Jupyter Notebook Standards

- Clear markdown documentation for each section
- Descriptive cell outputs and explanations
- Proper code organization and structure
- Include data validation and error handling

### Example Code Structure

```python
"""
Module for analyzing plant-bee interactions.

This module provides functions for processing and analyzing
pollinator data to support conservation efforts.
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier


def analyze_bee_preferences(
    data: pd.DataFrame,
    target_column: str = "nonnative_bee"
) -> Dict[str, float]:
    """
    Analyze bee species preferences using machine learning.
    
    Args:
        data: Input DataFrame with bee and plant data
        target_column: Column name for the target variable
        
    Returns:
        Dictionary containing feature importance scores
        
    Raises:
        ValueError: If required columns are missing
    """
    # Implementation here
    pass
```

## 🧪 Testing Guidelines

### Test Requirements

- **Unit tests**: Test individual functions and methods
- **Integration tests**: Test data processing pipelines
- **Notebook tests**: Ensure notebooks run without errors
- **Data validation tests**: Verify data integrity and quality

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pollinexus

# Run specific test file
pytest tests/test_data_processing.py

# Run notebook tests
pytest --nbval todo/project.ipynb
```

### Test Coverage

- Aim for at least 80% code coverage
- Focus on critical data processing functions
- Include edge cases and error conditions

## 📚 Documentation

### Documentation Standards

- **Docstrings**: Use Google or NumPy style docstrings
- **README updates**: Update when adding new features
- **API documentation**: Document all public functions
- **Tutorial notebooks**: Create examples for new features

### Documentation Structure

```
docs/
├── api.md              # API reference
├── tutorials/          # Tutorial notebooks
├── examples/           # Example scripts
└── research/           # Research notes and findings
```

## 🐛 Issue Reporting

### Bug Reports

When reporting bugs, please include:

1. **Clear description** of the problem
2. **Steps to reproduce** the issue
3. **Expected behavior** vs actual behavior
4. **Environment details** (OS, Python version, dependencies)
5. **Error messages** and stack traces
6. **Screenshots** if applicable

### Feature Requests

For feature requests, include:

1. **Problem statement** and use case
2. **Proposed solution** or approach
3. **Expected benefits** and impact
4. **Alternative solutions** considered
5. **Implementation suggestions** if applicable

## 🔄 Pull Request Process

### Before Submitting

1. **Ensure tests pass**: Run the full test suite
2. **Update documentation**: Add/update relevant docs
3. **Check code style**: Run linters and formatters
4. **Self-review**: Review your changes critically

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Test addition
- [ ] Refactoring

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Documentation
- [ ] README updated
- [ ] API docs updated
- [ ] Comments added to code

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] No debugging code left
- [ ] Error handling included
```

### Review Process

1. **Automated checks** must pass (CI/CD)
2. **Code review** by maintainers
3. **Address feedback** and make requested changes
4. **Final approval** from maintainers
5. **Merge** to main branch

## 🚀 Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **Major version**: Breaking changes
- **Minor version**: New features, backward compatible
- **Patch version**: Bug fixes, backward compatible

### Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version bumped
- [ ] Release notes prepared
- [ ] Tagged release created

## 🏆 Recognition

Contributors will be recognized in:

- **README.md** contributors section
- **Release notes** for significant contributions
- **Project documentation** for major features
- **Academic citations** for research contributions

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and ideas
- **Email**: For sensitive or private matters
- **Documentation**: Check existing docs first

## 🙏 Thank You

Thank you for contributing to pollinator conservation! Your work helps support environmental agencies and protect vital ecosystems.

---

**Remember**: Every contribution, no matter how small, makes a difference in pollinator conservation efforts. 