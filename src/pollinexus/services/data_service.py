"""
Data processing service for Pollinexus.

This service handles data loading, validation, cleaning, and analysis
with comprehensive logging and monitoring.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import logging
from datetime import datetime
import time

from ..core.logging import logger
from ..core.metrics import monitor_performance
from ..core.error_tracking import track_errors, error_tracker


class DataService:
    """Service for data processing operations with comprehensive logging."""
    
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.xls', '.parquet']
        logger.info("DataService initialized", extra={"supported_formats": self.supported_formats})
    
    @monitor_performance("data_load")
    @track_errors("data_load")
    def load_dataset(self, file_path: str) -> pd.DataFrame:
        """
        Load dataset from file with comprehensive logging.
        
        Args:
            file_path: Path to the dataset file
            
        Returns:
            pd.DataFrame: Loaded dataset
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        logger.info(
            "Starting dataset load operation",
            extra={"file_path": file_path, "operation": "data_load"}
        )
        
        path = Path(file_path)
        if not path.exists():
            logger.error(
                "File not found",
                extra={"file_path": file_path, "operation": "data_load"}
            )
            raise FileNotFoundError(f"File not found: {file_path}")
        
        start_time = time.time()
        
        try:
            if path.suffix.lower() == '.csv':
                logger.debug("Loading CSV file", extra={"file_path": file_path})
                data = pd.read_csv(file_path)
            elif path.suffix.lower() in ['.xlsx', '.xls']:
                logger.debug("Loading Excel file", extra={"file_path": file_path})
                data = pd.read_excel(file_path)
            elif path.suffix.lower() == '.parquet':
                logger.debug("Loading Parquet file", extra={"file_path": file_path})
                data = pd.read_parquet(file_path)
            else:
                logger.error(
                    "Unsupported file format",
                    extra={
                        "file_path": file_path,
                        "file_extension": path.suffix,
                        "supported_formats": self.supported_formats,
                        "operation": "data_load"
                    }
                )
                raise ValueError(f"Unsupported file format: {path.suffix}")
            
            load_time = time.time() - start_time
            
            logger.info(
                "Dataset loaded successfully",
                extra={
                    "file_path": file_path,
                    "rows": len(data),
                    "columns": len(data.columns),
                    "load_time": load_time,
                    "memory_usage_mb": data.memory_usage(deep=True).sum() / 1024 / 1024,
                    "operation": "data_load"
                }
            )
            
            return data
            
        except Exception as e:
            logger.error(
                "Dataset load failed",
                extra={"file_path": file_path, "error": str(e), "operation": "data_load"}
            )
            raise
    
    @monitor_performance("data_validation")
    @track_errors("data_validation")
    def validate_dataset(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate dataset structure and content with detailed logging.
        
        Args:
            data: DataFrame to validate
            
        Returns:
            Dict containing validation results
        """
        logger.info(
            "Starting dataset validation",
            extra={"rows": len(data), "columns": len(data.columns), "operation": "data_validation"}
        )
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'info': {},
            'validation_time': time.time()
        }
        
        try:
            # Check required columns
            required_columns = [
                'sample_id', 'bees_num', 'date', 'season', 'site',
                'native_or_non', 'sampling', 'plant_species', 'time',
                'bee_species', 'sex', 'specialized_on', 'parasitic',
                'nesting', 'status', 'nonnative_bee'
            ]
            
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"Missing required columns: {missing_columns}")
                logger.warning(
                    "Missing required columns detected",
                    extra={"missing_columns": missing_columns, "operation": "data_validation"}
                )
            
            # Check data types
            type_issues = []
            if 'bees_num' in data.columns and not pd.api.types.is_numeric_dtype(data['bees_num']):
                type_issues.append("bees_num should be numeric")
                validation_result['warnings'].append("bees_num should be numeric")
            
            if 'date' in data.columns:
                try:
                    pd.to_datetime(data['date'], errors='raise')
                except:
                    type_issues.append("date should be parseable as datetime")
                    validation_result['warnings'].append("date should be parseable as datetime")
            
            if type_issues:
                logger.warning(
                    "Data type issues detected",
                    extra={"type_issues": type_issues, "operation": "data_validation"}
                )
            
            # Check for missing values
            missing_counts = data.isnull().sum()
            total_missing = missing_counts.sum()
            
            if total_missing > 0:
                validation_result['info']['missing_values'] = missing_counts.to_dict()
                validation_result['info']['total_missing'] = int(total_missing)
                validation_result['info']['missing_percentage'] = float(total_missing / len(data) * 100)
                
                logger.info(
                    "Missing values detected",
                    extra={"total_missing": int(total_missing), "missing_percentage": float(total_missing / len(data) * 100), "missing_by_column": missing_counts.to_dict(), "operation": "data_validation"}
                )
            
            # Check for duplicates
            duplicate_count = data.duplicated().sum()
            if duplicate_count > 0:
                validation_result['warnings'].append(f"Found {duplicate_count} duplicate rows")
                validation_result['info']['duplicate_count'] = int(duplicate_count)
                
                logger.warning(
                    "Duplicate rows detected",
                    extra={"duplicate_count": int(duplicate_count), "operation": "data_validation"}
                )
            
            # Check data ranges
            range_issues = []
            if 'bees_num' in data.columns:
                bees_num_stats = data['bees_num'].describe()
                if bees_num_stats['min'] < 0:
                    range_issues.append("bees_num contains negative values")
                if bees_num_stats['max'] > 1000:  # Reasonable upper limit
                    range_issues.append("bees_num contains unusually high values")
                
                validation_result['info']['bees_num_stats'] = bees_num_stats.to_dict()
            
            if range_issues:
                validation_result['warnings'].extend(range_issues)
                logger.warning(
                    "Data range issues detected",
                    extra={"range_issues": range_issues, "operation": "data_validation"}
                )
            
            # Calculate validation summary
            validation_result['summary'] = {
                'total_rows': len(data),
                'total_columns': len(data.columns),
                'missing_columns_count': len(missing_columns),
                'type_issues_count': len(type_issues),
                'range_issues_count': len(range_issues),
                'duplicate_rows_count': int(duplicate_count),
                'total_missing_values': int(total_missing)
            }
            
            validation_time = time.time() - validation_result['validation_time']
            validation_result['validation_time'] = validation_time
            
            logger.info(
                "Dataset validation completed",
                extra={
                    "is_valid": validation_result['is_valid'],
                    "errors_count": len(validation_result['errors']),
                    "warnings_count": len(validation_result['warnings']),
                    "validation_time": validation_time,
                    "operation": "data_validation"
                }
            )
            
            return validation_result
            
        except Exception as e:
            logger.error(
                "Dataset validation failed",
                extra={"error": str(e), "operation": "data_validation"}
            )
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
            raise
    
    @monitor_performance("data_cleaning")
    @track_errors("data_cleaning")
    def clean_dataset(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and preprocess dataset with comprehensive logging.
        
        Args:
            data: DataFrame to clean
            
        Returns:
            pd.DataFrame: Cleaned dataset
        """
        logger.info(
            "Starting dataset cleaning",
            extra={"original_rows": len(data), "original_columns": len(data.columns), "operation": "data_cleaning"}
        )
        
        start_time = time.time()
        original_memory = data.memory_usage(deep=True).sum() / 1024 / 1024
        
        try:
            cleaned_data = data.copy()
            cleaning_steps = []
            
            # Convert data types
            if 'bees_num' in cleaned_data.columns:
                logger.debug("Converting bees_num to numeric", operation="data_cleaning")
                cleaned_data['bees_num'] = pd.to_numeric(cleaned_data['bees_num'], errors='coerce')
                cleaning_steps.append("converted_bees_num_to_numeric")
            
            if 'date' in cleaned_data.columns:
                logger.debug("Converting date to datetime", operation="data_cleaning")
                cleaned_data['date'] = pd.to_datetime(cleaned_data['date'], errors='coerce')
                cleaning_steps.append("converted_date_to_datetime")
            
            # Handle missing values
            logger.debug("Handling missing values", operation="data_cleaning")
            cleaned_data['plant_species'] = cleaned_data['plant_species'].fillna('None')
            cleaned_data['specialized_on'] = cleaned_data['specialized_on'].fillna('Unknown')
            cleaning_steps.append("filled_missing_values")
            
            # Remove duplicates
            original_duplicates = cleaned_data.duplicated().sum()
            if original_duplicates > 0:
                logger.debug("Removing duplicate rows", duplicate_count=original_duplicates, operation="data_cleaning")
                cleaned_data = cleaned_data.drop_duplicates()
                cleaning_steps.append("removed_duplicates")
            
            # Handle outliers in bees_num
            if 'bees_num' in cleaned_data.columns:
                Q1 = cleaned_data['bees_num'].quantile(0.25)
                Q3 = cleaned_data['bees_num'].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers_mask = (cleaned_data['bees_num'] < lower_bound) | (cleaned_data['bees_num'] > upper_bound)
                outliers_count = outliers_mask.sum()
                
                if outliers_count > 0:
                    logger.debug(
                        "Handling outliers in bees_num",
                        extra={"outliers_count": int(outliers_count), "lower_bound": float(lower_bound), "upper_bound": float(upper_bound), "operation": "data_cleaning"}
                    )
                    # Cap outliers instead of removing them
                    cleaned_data.loc[cleaned_data['bees_num'] < lower_bound, 'bees_num'] = lower_bound
                    cleaned_data.loc[cleaned_data['bees_num'] > upper_bound, 'bees_num'] = upper_bound
                    cleaning_steps.append("capped_outliers")
            
            # Standardize text columns
            text_columns = ['bee_species', 'plant_species', 'site', 'season']
            for col in text_columns:
                if col in cleaned_data.columns:
                    logger.debug(f"Standardizing {col}", operation="data_cleaning")
                    cleaned_data[col] = cleaned_data[col].astype(str).str.strip().str.title()
            
            cleaning_steps.append("standardized_text_columns")
            
            # Calculate cleaning statistics
            cleaning_time = time.time() - start_time
            final_memory = cleaned_data.memory_usage(deep=True).sum() / 1024 / 1024
            
            cleaning_stats = {
                'original_rows': len(data),
                'cleaned_rows': len(cleaned_data),
                'rows_removed': len(data) - len(cleaned_data),
                'original_memory_mb': original_memory,
                'final_memory_mb': final_memory,
                'memory_change_mb': final_memory - original_memory,
                'cleaning_time': cleaning_time,
                'cleaning_steps': cleaning_steps
            }
            
            logger.info(
                "Dataset cleaning completed successfully",
                **cleaning_stats,
                operation="data_cleaning"
            )
            
            return cleaned_data
            
        except Exception as e:
            logger.error(
                "Dataset cleaning failed",
                extra={"error": str(e), "operation": "data_cleaning"}
            )
            raise
    
    @monitor_performance("dataset_info")
    @track_errors("dataset_info")
    def get_dataset_info(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Get comprehensive dataset statistics and information.
        
        Args:
            data: DataFrame to analyze
            
        Returns:
            Dict containing dataset information
        """
        logger.info(
            "Generating dataset information",
            rows=len(data),
            columns=len(data.columns),
            operation="dataset_info"
        )
        
        try:
            info = {
                'total_records': len(data),
                'total_columns': len(data.columns),
                'missing_values': data.isnull().sum().to_dict(),
                'unique_values': {},
                'data_types': data.dtypes.to_dict(),
                'memory_usage_mb': data.memory_usage(deep=True).sum() / 1024 / 1024,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # Count unique values for categorical columns
            categorical_columns = ['bee_species', 'plant_species', 'site', 'season']
            for col in categorical_columns:
                if col in data.columns:
                    unique_count = data[col].nunique()
                    info['unique_values'][col] = unique_count
                    
                    # Get top values for each categorical column
                    top_values = data[col].value_counts().head(5).to_dict()
                    info[f'{col}_top_values'] = top_values
            
            # Numeric column statistics
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            if len(numeric_columns) > 0:
                info['numeric_stats'] = data[numeric_columns].describe().to_dict()
            
            # Date column analysis
            date_columns = data.select_dtypes(include=['datetime64']).columns
            if len(date_columns) > 0:
                info['date_stats'] = {}
                for col in date_columns:
                    info['date_stats'][col] = {
                        'min': data[col].min().isoformat() if pd.notna(data[col].min()) else None,
                        'max': data[col].max().isoformat() if pd.notna(data[col].max()) else None,
                        'missing_count': data[col].isnull().sum()
                    }
            
            # Data quality metrics
            info['quality_metrics'] = {
                'completeness': (1 - data.isnull().sum().sum() / (len(data) * len(data.columns))) * 100,
                'duplicate_rows': data.duplicated().sum(),
                'duplicate_percentage': (data.duplicated().sum() / len(data)) * 100
            }
            
            logger.info(
                "Dataset information generated successfully",
                total_records=info['total_records'],
                total_columns=info['total_columns'],
                memory_usage_mb=info['memory_usage_mb'],
                completeness_percentage=info['quality_metrics']['completeness'],
                operation="dataset_info"
            )
            
            return info
            
        except Exception as e:
            logger.error(
                "Dataset information generation failed",
                extra={"error": str(e), "operation": "dataset_info"}
            )
            raise
    
    @monitor_performance("data_export")
    @track_errors("data_export")
    def export_dataset(self, data: pd.DataFrame, output_path: str, format: str = 'csv') -> Dict[str, Any]:
        """
        Export dataset to various formats with logging.
        
        Args:
            data: DataFrame to export
            output_path: Path for output file
            format: Export format ('csv', 'excel', 'parquet', 'json')
            
        Returns:
            Dict containing export information
        """
        logger.info(
            "Starting dataset export",
            extra={"output_path": output_path, "format": format, "rows": len(data), "columns": len(data.columns), "operation": "data_export"}
        )
        
        start_time = time.time()
        
        try:
            if format.lower() == 'csv':
                data.to_csv(output_path, index=False)
            elif format.lower() == 'excel':
                data.to_excel(output_path, index=False)
            elif format.lower() == 'parquet':
                data.to_parquet(output_path, index=False)
            elif format.lower() == 'json':
                data.to_json(output_path, orient='records', indent=2)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            export_time = time.time() - start_time
            file_size = Path(output_path).stat().st_size / 1024 / 1024  # MB
            
            export_info = {
                'output_path': output_path,
                'format': format,
                'rows_exported': len(data),
                'columns_exported': len(data.columns),
                'file_size_mb': file_size,
                'export_time': export_time,
                'exported_at': datetime.utcnow().isoformat()
            }
            
            logger.info(
                "Dataset export completed successfully",
                **export_info,
                operation="data_export"
            )
            
            return export_info
            
        except Exception as e:
            logger.error(
                "Dataset export failed",
                extra={"output_path": output_path, "format": format, "error": str(e), "operation": "data_export"}
            )
            raise
    
    @monitor_performance("data_sampling")
    @track_errors("data_sampling")
    def sample_dataset(self, data: pd.DataFrame, sample_size: int = 1000, random_state: int = 42) -> pd.DataFrame:
        """
        Create a random sample of the dataset for testing/development.
        
        Args:
            data: DataFrame to sample
            sample_size: Number of rows to sample
            random_state: Random seed for reproducibility
            
        Returns:
            pd.DataFrame: Sampled dataset
        """
        logger.info(
            "Creating dataset sample",
            extra={"original_rows": len(data), "sample_size": sample_size, "random_state": random_state, "operation": "data_sampling"}
        )
        
        try:
            if sample_size >= len(data):
                logger.warning(
                    "Sample size larger than dataset, returning full dataset",
                    extra={"sample_size": sample_size, "dataset_size": len(data), "operation": "data_sampling"}
                )
                return data
            
            sampled_data = data.sample(n=sample_size, random_state=random_state)
            
            logger.info(
                "Dataset sample created successfully",
                extra={"original_rows": len(data), "sampled_rows": len(sampled_data), "sample_percentage": (len(sampled_data) / len(data)) * 100, "operation": "data_sampling"}
            )
            
            return sampled_data
            
        except Exception as e:
            logger.error(
                "Dataset sampling failed",
                extra={"error": str(e), "operation": "data_sampling"}
            )
            raise 