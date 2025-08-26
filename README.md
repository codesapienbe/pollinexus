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
├── assets/                  # Static assets (images, etc.)
├── docs/                    # Documentation
│   ├── LICENSE.md          # Project license
│   ├── CONTRIBUTING.md     # Contribution guidelines
│   ├── CODE_OF_CONDUCT.md  # Community standards
│   └── API.md              # API documentation
├── src/                     # Source code
│   └── pollinexus/         # Main package
├── test/                    # Test suite
└── todo/                    # Analysis files
    ├── project.ipynb       # Main analysis notebook
    └── plants_and_bees.csv # Dataset
```

## 🔬 Analysis Components

### 1. Data Cleaning

- Convert columns to appropriate data types
- Handle missing values
- Validate data integrity

### 2. Machine Learning Analysis

- Train models to identify plant preferences
- Compare native vs non-native bee species behavior
- Feature importance analysis

### 3. Visualization

- Bee and plant species distribution charts
- Seasonal patterns analysis
- Site comparison visualizations

### 4. Recommendations

- Top 3 plant species for native bee support
- Conservation strategy recommendations
- Implementation guidelines

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
