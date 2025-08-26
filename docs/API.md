# Pollinexus API Documentation

## Overview

The Pollinexus API provides programmatic access to pollinator data analysis tools and machine learning models for environmental conservation research.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Modules](#core-modules)
- [Data Processing](#data-processing)
- [Machine Learning](#machine-learning)
- [Visualization](#visualization)
- [Utilities](#utilities)
- [Examples](#examples)

## Installation

```bash
pip install pollinexus
```

## Quick Start

```python
import pollinexus as px
import pandas as pd

# Load and clean data
data = px.load_data("plants_and_bees.csv")
clean_data = px.clean_dataset(data)

# Analyze bee preferences
preferences = px.analyze_bee_preferences(clean_data)

# Generate recommendations
recommendations = px.get_plant_recommendations(clean_data, top_n=3)

# Create visualizations
px.plot_bee_distribution(clean_data)
```

## Core Modules

### Data Loading and Validation

#### `load_data(file_path: str) -> pd.DataFrame`

Load pollinator data from CSV file.

**Parameters:**
- `file_path` (str): Path to the CSV file

**Returns:**
- `pd.DataFrame`: Loaded dataset

**Example:**
```python
data = px.load_data("plants_and_bees.csv")
print(f"Loaded {len(data)} records")
```

#### `validate_data(data: pd.DataFrame) -> Dict[str, Any]`

Validate data integrity and structure.

**Parameters:**
- `data` (pd.DataFrame): Input dataset

**Returns:**
- `Dict[str, Any]`: Validation results including errors and warnings

**Example:**
```python
validation = px.validate_data(data)
if validation['is_valid']:
    print("Data validation passed")
else:
    print(f"Validation errors: {validation['errors']}")
```

### Data Cleaning

#### `clean_dataset(data: pd.DataFrame) -> pd.DataFrame`

Clean and preprocess the pollinator dataset.

**Parameters:**
- `data` (pd.DataFrame): Raw dataset

**Returns:**
- `pd.DataFrame`: Cleaned dataset

**Features:**
- Converts data types
- Handles missing values
- Removes duplicates
- Validates date formats
- Standardizes categorical variables

**Example:**
```python
clean_data = px.clean_dataset(data)
print(f"Cleaned dataset shape: {clean_data.shape}")
```

#### `handle_missing_values(data: pd.DataFrame, strategy: str = 'auto') -> pd.DataFrame`

Handle missing values using specified strategy.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `strategy` (str): Strategy for handling missing values
  - 'auto': Automatic strategy selection
  - 'drop': Remove rows with missing values
  - 'fill': Fill with appropriate values
  - 'interpolate': Interpolate missing values

**Returns:**
- `pd.DataFrame`: Dataset with missing values handled

**Example:**
```python
cleaned = px.handle_missing_values(data, strategy='fill')
```

## Machine Learning

### Bee Preference Analysis

#### `analyze_bee_preferences(data: pd.DataFrame, target_column: str = 'nonnative_bee') -> Dict[str, Any]`

Analyze bee species preferences using machine learning.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `target_column` (str): Target variable column name

**Returns:**
- `Dict[str, Any]`: Analysis results including:
  - `model`: Trained model
  - `feature_importance`: Feature importance scores
  - `accuracy`: Model accuracy
  - `predictions`: Model predictions

**Example:**
```python
results = px.analyze_bee_preferences(clean_data)
print(f"Model accuracy: {results['accuracy']:.3f}")
```

#### `train_preference_model(data: pd.DataFrame, model_type: str = 'random_forest') -> Any`

Train a machine learning model for bee preference prediction.

**Parameters:**
- `data` (pd.DataFrame): Training dataset
- `model_type` (str): Type of model to train
  - 'random_forest': Random Forest Classifier
  - 'logistic_regression': Logistic Regression
  - 'svm': Support Vector Machine
  - 'neural_network': Neural Network

**Returns:**
- Trained model object

**Example:**
```python
model = px.train_preference_model(clean_data, model_type='random_forest')
```

### Plant Recommendation System

#### `get_plant_recommendations(data: pd.DataFrame, top_n: int = 3, criteria: str = 'native_bee_support') -> List[Dict[str, Any]]`

Generate plant species recommendations for pollinator conservation.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `top_n` (int): Number of top recommendations to return
- `criteria` (str): Recommendation criteria
  - 'native_bee_support': Support for native bee species
  - 'diversity': Plant species diversity
  - 'seasonal_coverage': Year-round flowering
  - 'abundance': High bee abundance

**Returns:**
- `List[Dict[str, Any]]`: List of recommended plants with details

**Example:**
```python
recommendations = px.get_plant_recommendations(clean_data, top_n=5)
for plant in recommendations:
    print(f"{plant['species']}: {plant['score']:.3f}")
```

#### `calculate_plant_scores(data: pd.DataFrame) -> pd.DataFrame`

Calculate preference scores for all plant species.

**Parameters:**
- `data` (pd.DataFrame): Input dataset

**Returns:**
- `pd.DataFrame`: Plant species with their preference scores

**Example:**
```python
scores = px.calculate_plant_scores(clean_data)
print(scores.head())
```

## Visualization

### Distribution Plots

#### `plot_bee_distribution(data: pd.DataFrame, group_by: str = 'bee_species') -> matplotlib.figure.Figure`

Create distribution plots for bee species.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `group_by` (str): Grouping variable for the plot

**Returns:**
- `matplotlib.figure.Figure`: Generated plot

**Example:**
```python
fig = px.plot_bee_distribution(clean_data, group_by='site')
fig.show()
```

#### `plot_plant_distribution(data: pd.DataFrame, top_n: int = 10) -> matplotlib.figure.Figure`

Create distribution plots for plant species.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `top_n` (int): Number of top plants to display

**Returns:**
- `matplotlib.figure.Figure`: Generated plot

**Example:**
```python
fig = px.plot_plant_distribution(clean_data, top_n=15)
fig.show()
```

### Seasonal Analysis

#### `plot_seasonal_patterns(data: pd.DataFrame) -> matplotlib.figure.Figure`

Visualize seasonal patterns in bee and plant activity.

**Parameters:**
- `data` (pd.DataFrame): Input dataset

**Returns:**
- `matplotlib.figure.Figure`: Generated plot

**Example:**
```python
fig = px.plot_seasonal_patterns(clean_data)
fig.show()
```

#### `plot_site_comparison(data: pd.DataFrame) -> matplotlib.figure.Figure`

Compare bee and plant diversity across different sites.

**Parameters:**
- `data` (pd.DataFrame): Input dataset

**Returns:**
- `matplotlib.figure.Figure`: Generated plot

**Example:**
```python
fig = px.plot_site_comparison(clean_data)
fig.show()
```

### Interactive Visualizations

#### `create_interactive_dashboard(data: pd.DataFrame) -> plotly.graph_objects.Figure`

Create an interactive dashboard for data exploration.

**Parameters:**
- `data` (pd.DataFrame): Input dataset

**Returns:**
- `plotly.graph_objects.Figure`: Interactive dashboard

**Example:**
```python
dashboard = px.create_interactive_dashboard(clean_data)
dashboard.show()
```

## Utilities

### Data Export

#### `export_results(results: Dict[str, Any], output_path: str, format: str = 'json') -> None`

Export analysis results to various formats.

**Parameters:**
- `results` (Dict[str, Any]): Analysis results
- `output_path` (str): Output file path
- `format` (str): Output format ('json', 'csv', 'excel', 'html')

**Example:**
```python
px.export_results(results, 'analysis_results.json')
```

### Statistical Analysis

#### `calculate_diversity_indices(data: pd.DataFrame) -> Dict[str, float]`

Calculate biodiversity indices for the dataset.

**Parameters:**
- `data` (pd.DataFrame): Input dataset

**Returns:**
- `Dict[str, float]`: Diversity indices including Shannon, Simpson, etc.

**Example:**
```python
indices = px.calculate_diversity_indices(clean_data)
print(f"Shannon diversity: {indices['shannon']:.3f}")
```

#### `perform_statistical_tests(data: pd.DataFrame, test_type: str = 'chi_square') -> Dict[str, Any]`

Perform statistical tests on the data.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `test_type` (str): Type of statistical test

**Returns:**
- `Dict[str, Any]`: Test results including p-values and statistics

**Example:**
```python
test_results = px.perform_statistical_tests(clean_data, 'chi_square')
print(f"P-value: {test_results['p_value']:.4f}")
```

## Examples

### Complete Analysis Pipeline

```python
import pollinexus as px
import pandas as pd

# 1. Load and validate data
data = px.load_data("plants_and_bees.csv")
validation = px.validate_data(data)

if not validation['is_valid']:
    print("Data validation failed")
    exit(1)

# 2. Clean dataset
clean_data = px.clean_dataset(data)

# 3. Analyze bee preferences
preferences = px.analyze_bee_preferences(clean_data)
print(f"Model accuracy: {preferences['accuracy']:.3f}")

# 4. Generate recommendations
recommendations = px.get_plant_recommendations(clean_data, top_n=3)
print("Top 3 recommended plants:")
for i, plant in enumerate(recommendations, 1):
    print(f"{i}. {plant['species']} (Score: {plant['score']:.3f})")

# 5. Create visualizations
fig1 = px.plot_bee_distribution(clean_data)
fig1.savefig('bee_distribution.png')

fig2 = px.plot_seasonal_patterns(clean_data)
fig2.savefig('seasonal_patterns.png')

# 6. Export results
results = {
    'preferences': preferences,
    'recommendations': recommendations,
    'diversity': px.calculate_diversity_indices(clean_data)
}
px.export_results(results, 'pollinexus_analysis.json')
```

### Custom Analysis

```python
# Custom machine learning analysis
model = px.train_preference_model(clean_data, model_type='neural_network')

# Custom visualization
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(12, 10))
px.plot_bee_distribution(clean_data, ax=axes[0,0])
px.plot_plant_distribution(clean_data, ax=axes[0,1])
px.plot_seasonal_patterns(clean_data, ax=axes[1,0])
px.plot_site_comparison(clean_data, ax=axes[1,1])

plt.tight_layout()
plt.show()
```

## Error Handling

The API includes comprehensive error handling:

```python
try:
    data = px.load_data("nonexistent_file.csv")
except FileNotFoundError:
    print("Data file not found")
except ValueError as e:
    print(f"Data validation error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Considerations

- Large datasets (>100,000 rows) may require additional memory
- Machine learning models are cached for reuse
- Visualizations use efficient plotting libraries
- Data processing is optimized for typical pollinator datasets

## Contributing

To contribute to the API:

1. Follow the [Contributing Guidelines](../CONTRIBUTING.md)
2. Add comprehensive docstrings to new functions
3. Include unit tests for new features
4. Update this documentation for API changes

## Support

For API support and questions:

- Check the [GitHub Issues](https://github.com/your-username/pollinexus/issues)
- Review the [Examples](../examples/) directory
- Consult the [Tutorials](../tutorials/) for detailed guides 