"""
Data processing tasks for Pollinexus.

This module contains Celery tasks for data processing operations
with comprehensive logging and monitoring.
"""

from celery import current_task
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import time
import uuid
from pathlib import Path

from ..services.data_service import DataService
from ..services.database_service import DatabaseService
from ..services.duckdb_service import DuckDBService
from ..core.database import SessionLocal
from ..core.logging import logger, correlation_id
from ..core.metrics import monitor_performance
from ..core.error_tracking import track_errors, error_tracker
from .celery_app import celery_app


@celery_app.task(bind=True, name='pollinexus.tasks.data_processing.process_dataset')
@monitor_performance("celery_dataset_processing")
@track_errors("celery_data_processing")
def process_dataset(self, dataset_id: int, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Process and clean a dataset with comprehensive logging.
    
    Args:
        dataset_id: ID of the dataset to process
        parameters: Processing parameters
        
    Returns:
        Dict containing processing results
    """
    
    task_correlation_id = str(uuid.uuid4())
    correlation_id.set(task_correlation_id)
    
    logger.info(
        "Starting dataset processing",
        task_id=self.request.id,
        dataset_id=dataset_id,
        parameters=parameters,
        correlation_id=task_correlation_id,
        operation="celery_dataset_processing"
    )
    
    db = None
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Loading dataset',
                'correlation_id': task_correlation_id,
                'progress': 10
            }
        )
        
        # Get dataset
        db = SessionLocal()
        db_service = DatabaseService(db)
        dataset = db_service.get_dataset(dataset_id)
        
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        # Load dataset
        data_service = DataService()
        data = data_service.load_dataset(dataset.file_path)
        
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Validating dataset',
                'correlation_id': task_correlation_id,
                'progress': 30
            }
        )
        
        # Validate dataset
        validation_result = data_service.validate_dataset(data)
        
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Cleaning dataset',
                'correlation_id': task_correlation_id,
                'progress': 50
            }
        )
        
        # Clean dataset
        cleaned_data = data_service.clean_dataset(data)
        
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Generating dataset info',
                'correlation_id': task_correlation_id,
                'progress': 70
            }
        )
        
        # Get dataset information
        dataset_info = data_service.get_dataset_info(cleaned_data)
        
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Saving processed data',
                'correlation_id': task_correlation_id,
                'progress': 90
            }
        )
        
        # Save processed data
        processed_filename = f"processed_dataset_{dataset_id}_{int(time.time())}.csv"
        processed_path = Path("processed_data") / processed_filename
        processed_path.parent.mkdir(exist_ok=True)
        
        export_info = data_service.export_dataset(cleaned_data, str(processed_path), 'csv')
        
        # Prepare results
        results = {
            'original_rows': len(data),
            'processed_rows': len(cleaned_data),
            'rows_removed': len(data) - len(cleaned_data),
            'validation_result': validation_result,
            'dataset_info': dataset_info,
            'processed_file_path': str(processed_path),
            'export_info': export_info,
            'parameters': parameters or {},
            'correlation_id': task_correlation_id
        }
        
        logger.info(
            "Dataset processing completed successfully",
            task_id=self.request.id,
            dataset_id=dataset_id,
            original_rows=len(data),
            processed_rows=len(cleaned_data),
            processed_file=str(processed_path),
            correlation_id=task_correlation_id,
            operation="celery_dataset_processing"
        )
        
        return results
        
    except Exception as e:
        logger.error(
            "Dataset processing failed",
            task_id=self.request.id,
            dataset_id=dataset_id,
            error=str(e),
            correlation_id=task_correlation_id,
            operation="celery_dataset_processing"
        )
        raise
    finally:
        if db:
            db.close()
        correlation_id.set(None)


@celery_app.task(bind=True, name='pollinexus.tasks.data_processing.export_dataset')
@monitor_performance("celery_dataset_export")
@track_errors("celery_data_processing")
def export_dataset(self, dataset_id: int, format: str = 'csv', 
                   parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Export dataset to various formats.
    
    Args:
        dataset_id: ID of the dataset to export
        format: Export format ('csv', 'excel', 'parquet', 'json')
        parameters: Export parameters
        
    Returns:
        Dict containing export results
    """
    
    task_correlation_id = str(uuid.uuid4())
    correlation_id.set(task_correlation_id)
    
    logger.info(
        "Starting dataset export",
        task_id=self.request.id,
        dataset_id=dataset_id,
        format=format,
        parameters=parameters,
        correlation_id=task_correlation_id,
        operation="celery_dataset_export"
    )
    
    db = None
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Loading dataset',
                'correlation_id': task_correlation_id,
                'progress': 20
            }
        )
        
        # Get dataset
        db = SessionLocal()
        db_service = DatabaseService(db)
        dataset = db_service.get_dataset(dataset_id)
        
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        # Load and clean data
        data_service = DataService()
        data = data_service.load_dataset(dataset.file_path)
        cleaned_data = data_service.clean_dataset(data)
        
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Exporting data',
                'correlation_id': task_correlation_id,
                'progress': 60
            }
        )
        
        # Export data
        export_filename = f"export_{dataset_id}_{int(time.time())}.{format}"
        export_path = Path("exports") / export_filename
        export_path.parent.mkdir(exist_ok=True)
        
        export_info = data_service.export_dataset(cleaned_data, str(export_path), format)
        
        # Prepare results
        results = {
            'export_format': format,
            'export_path': str(export_path),
            'export_filename': export_filename,
            'export_info': export_info,
            'parameters': parameters or {},
            'correlation_id': task_correlation_id
        }
        
        logger.info(
            "Dataset export completed successfully",
            task_id=self.request.id,
            dataset_id=dataset_id,
            format=format,
            export_path=str(export_path),
            file_size_mb=export_info['file_size_mb'],
            correlation_id=task_correlation_id,
            operation="celery_dataset_export"
        )
        
        return results
        
    except Exception as e:
        logger.error(
            "Dataset export failed",
            task_id=self.request.id,
            dataset_id=dataset_id,
            format=format,
            error=str(e),
            correlation_id=task_correlation_id,
            operation="celery_dataset_export"
        )
        raise
    finally:
        if db:
            db.close()
        correlation_id.set(None)


@celery_app.task(bind=True, name='pollinexus.tasks.data_processing.sample_dataset')
@monitor_performance("celery_dataset_sampling")
@track_errors("celery_data_processing")
def sample_dataset(self, dataset_id: int, sample_size: int = 1000, 
                   random_state: int = 42, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create a random sample of the dataset.
    
    Args:
        dataset_id: ID of the dataset to sample
        sample_size: Number of rows to sample
        random_state: Random seed for reproducibility
        parameters: Sampling parameters
        
    Returns:
        Dict containing sampling results
    """
    
    task_correlation_id = str(uuid.uuid4())
    correlation_id.set(task_correlation_id)
    
    logger.info(
        "Starting dataset sampling",
        task_id=self.request.id,
        dataset_id=dataset_id,
        sample_size=sample_size,
        random_state=random_state,
        parameters=parameters,
        correlation_id=task_correlation_id,
        operation="celery_dataset_sampling"
    )
    
    db = None
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Loading dataset',
                'correlation_id': task_correlation_id,
                'progress': 20
            }
        )
        
        # Get dataset
        db = SessionLocal()
        db_service = DatabaseService(db)
        dataset = db_service.get_dataset(dataset_id)
        
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        # Load and clean data
        data_service = DataService()
        data = data_service.load_dataset(dataset.file_path)
        cleaned_data = data_service.clean_dataset(data)
        
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Creating sample',
                'correlation_id': task_correlation_id,
                'progress': 60
            }
        )
        
        # Create sample
        sampled_data = data_service.sample_dataset(cleaned_data, sample_size, random_state)
        
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Saving sample',
                'correlation_id': task_correlation_id,
                'progress': 80
            }
        )
        
        # Save sample
        sample_filename = f"sample_{dataset_id}_{sample_size}_{int(time.time())}.csv"
        sample_path = Path("samples") / sample_filename
        sample_path.parent.mkdir(exist_ok=True)
        
        export_info = data_service.export_dataset(sampled_data, str(sample_path), 'csv')
        
        # Prepare results
        results = {
            'original_rows': len(cleaned_data),
            'sampled_rows': len(sampled_data),
            'sample_size': sample_size,
            'random_state': random_state,
            'sample_path': str(sample_path),
            'sample_filename': sample_filename,
            'export_info': export_info,
            'parameters': parameters or {},
            'correlation_id': task_correlation_id
        }
        
        logger.info(
            "Dataset sampling completed successfully",
            task_id=self.request.id,
            dataset_id=dataset_id,
            original_rows=len(cleaned_data),
            sampled_rows=len(sampled_data),
            sample_path=str(sample_path),
            correlation_id=task_correlation_id,
            operation="celery_dataset_sampling"
        )
        
        return results
        
    except Exception as e:
        logger.error(
            "Dataset sampling failed",
            task_id=self.request.id,
            dataset_id=dataset_id,
            sample_size=sample_size,
            error=str(e),
            correlation_id=task_correlation_id,
            operation="celery_dataset_sampling"
        )
        raise
    finally:
        if db:
            db.close()
        correlation_id.set(None)


@celery_app.task(bind=True, name='pollinexus.tasks.data_processing.validate_dataset')
@monitor_performance("celery_dataset_validation")
@track_errors("celery_data_processing")
def validate_dataset(self, dataset_id: int, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Validate dataset structure and content.
    
    Args:
        dataset_id: ID of the dataset to validate
        parameters: Validation parameters
        
    Returns:
        Dict containing validation results
    """
    
    task_correlation_id = str(uuid.uuid4())
    correlation_id.set(task_correlation_id)
    
    logger.info(
        "Starting dataset validation",
        task_id=self.request.id,
        dataset_id=dataset_id,
        parameters=parameters,
        correlation_id=task_correlation_id,
        operation="celery_dataset_validation"
    )
    
    db = None
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Loading dataset',
                'correlation_id': task_correlation_id,
                'progress': 30
            }
        )
        
        # Get dataset
        db = SessionLocal()
        db_service = DatabaseService(db)
        dataset = db_service.get_dataset(dataset_id)
        
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        # Load dataset
        data_service = DataService()
        data = data_service.load_dataset(dataset.file_path)
        
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Validating dataset',
                'correlation_id': task_correlation_id,
                'progress': 70
            }
        )
        
        # Validate dataset
        validation_result = data_service.validate_dataset(data)
        
        # Get dataset information
        dataset_info = data_service.get_dataset_info(data)
        
        # Prepare results
        results = {
            'validation_result': validation_result,
            'dataset_info': dataset_info,
            'is_valid': validation_result['is_valid'],
            'errors_count': len(validation_result['errors']),
            'warnings_count': len(validation_result['warnings']),
            'parameters': parameters or {},
            'correlation_id': task_correlation_id
        }
        
        logger.info(
            "Dataset validation completed",
            task_id=self.request.id,
            dataset_id=dataset_id,
            is_valid=validation_result['is_valid'],
            errors_count=len(validation_result['errors']),
            warnings_count=len(validation_result['warnings']),
            correlation_id=task_correlation_id,
            operation="celery_dataset_validation"
        )
        
        return results
        
    except Exception as e:
        logger.error(
            "Dataset validation failed",
            task_id=self.request.id,
            dataset_id=dataset_id,
            error=str(e),
            correlation_id=task_correlation_id,
            operation="celery_dataset_validation"
        )
        raise
    finally:
        if db:
            db.close()
        correlation_id.set(None) 