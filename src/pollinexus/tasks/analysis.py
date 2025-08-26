"""
Analysis tasks for Pollinexus.

This module contains Celery tasks for data analysis operations
with comprehensive logging and monitoring.
"""

from celery import current_task
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
import time
import uuid

from ..services.data_service import DataService
from ..services.database_service import DatabaseService
from ..services.duckdb_service import DuckDBService
from ..core.database import SessionLocal
from ..core.logging import logger, correlation_id
from ..core.metrics import monitor_performance
from ..core.error_tracking import track_errors, error_tracker
from .celery_app import celery_app


@celery_app.task(bind=True, name='pollinexus.tasks.analysis.analyze_bee_preferences')
@monitor_performance("celery_bee_analysis")
@track_errors("celery_analysis")
def analyze_bee_preferences(self, dataset_id: int, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Analyze bee species preferences using machine learning.
    
    Args:
        dataset_id: ID of the dataset to analyze
        parameters: Analysis parameters
        
    Returns:
        Dict containing analysis results
    """
    
    # Generate correlation ID for task tracking
    task_correlation_id = str(uuid.uuid4())
    correlation_id.set(task_correlation_id)
    
    logger.info(
        "Starting bee preference analysis task",
        task_id=self.request.id,
        dataset_id=dataset_id,
        parameters=parameters,
        correlation_id=task_correlation_id,
        operation="celery_bee_analysis"
    )
    
    db = None
    try:
        # Update task status
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
            error_msg = f"Dataset {dataset_id} not found"
            logger.error(
                "Dataset not found for analysis",
                task_id=self.request.id,
                dataset_id=dataset_id,
                correlation_id=task_correlation_id
            )
            raise ValueError(error_msg)
        
        # Load and clean data
        data_service = DataService()
        data = data_service.load_dataset(dataset.file_path)
        cleaned_data = data_service.clean_dataset(data)
        
        logger.info(
            "Dataset loaded and cleaned",
            task_id=self.request.id,
            dataset_id=dataset_id,
            original_rows=len(data),
            cleaned_rows=len(cleaned_data),
            correlation_id=task_correlation_id
        )
        
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Preparing features',
                'correlation_id': task_correlation_id,
                'progress': 30
            }
        )
        
        # Prepare features for ML
        logger.debug(
            "Preparing features for ML",
            task_id=self.request.id,
            dataset_id=dataset_id,
            correlation_id=task_correlation_id
        )
        
        # Feature engineering
        features = cleaned_data[['bees_num', 'season', 'site', 'native_or_non']].copy()
        target = cleaned_data['nonnative_bee']
        
        # Encode categorical variables
        label_encoders = {}
        for col in ['season', 'site', 'native_or_non']:
            if col in features.columns:
                le = LabelEncoder()
                features[col] = le.fit_transform(features[col].astype(str))
                label_encoders[col] = le
        
        # Handle missing values
        features = features.fillna(0)
        target = target.fillna(0)
        
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Training model',
                'correlation_id': task_correlation_id,
                'progress': 50
            }
        )
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features, target, test_size=0.2, random_state=42
        )
        
        logger.debug(
            "Data split completed",
            task_id=self.request.id,
            train_size=len(X_train),
            test_size=len(X_test),
            correlation_id=task_correlation_id
        )
        
        # Train model
        model_params = parameters.get('model_params', {}) if parameters else {}
        model = RandomForestClassifier(
            n_estimators=model_params.get('n_estimators', 100),
            max_depth=model_params.get('max_depth', None),
            random_state=42,
            **{k: v for k, v in model_params.items() if k not in ['n_estimators', 'max_depth']}
        )
        
        model.fit(X_train, y_train)
        
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Evaluating model',
                'correlation_id': task_correlation_id,
                'progress': 70
            }
        )
        
        # Make predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        classification_rep = classification_report(y_test, y_pred, output_dict=True)
        
        # Cross-validation
        cv_scores = cross_val_score(model, features, target, cv=5, scoring='accuracy')
        
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Generating results',
                'correlation_id': task_correlation_id,
                'progress': 90
            }
        )
        
        # Prepare results
        results = {
            'accuracy': float(accuracy),
            'cv_mean_accuracy': float(cv_scores.mean()),
            'cv_std_accuracy': float(cv_scores.std()),
            'feature_importance': dict(zip(features.columns, model.feature_importances_)),
            'classification_report': classification_rep,
            'model_type': 'RandomForestClassifier',
            'model_params': model.get_params(),
            'label_encoders': {k: list(v.classes_) for k, v in label_encoders.items()},
            'data_info': {
                'total_samples': len(cleaned_data),
                'train_samples': len(X_train),
                'test_samples': len(X_test),
                'features_count': len(features.columns)
            },
            'parameters': parameters or {},
            'correlation_id': task_correlation_id
        }
        
        # Update job status
        db_service.update_job_status(
            self.request.id, 
            'completed', 
            results,
            celery_task_id=self.request.id
        )
        
        logger.info(
            "Bee preference analysis completed successfully",
            task_id=self.request.id,
            dataset_id=dataset_id,
            accuracy=accuracy,
            cv_accuracy=cv_scores.mean(),
            correlation_id=task_correlation_id,
            operation="celery_bee_analysis"
        )
        
        return results
        
    except Exception as e:
        logger.error(
            "Bee preference analysis task failed",
            task_id=self.request.id,
            dataset_id=dataset_id,
            error=str(e),
            correlation_id=task_correlation_id,
            operation="celery_bee_analysis"
        )
        
        # Update job status to failed
        if db:
            db_service.update_job_status(
                self.request.id, 
                'failed', 
                {'error': str(e), 'correlation_id': task_correlation_id},
                celery_task_id=self.request.id
            )
        
        raise
    finally:
        if db:
            db.close()
        correlation_id.set(None)


@celery_app.task(bind=True, name='pollinexus.tasks.analysis.generate_plant_recommendations')
@monitor_performance("celery_plant_recommendations")
@track_errors("celery_analysis")
def generate_plant_recommendations(self, dataset_id: int, top_n: int = 3, 
                                 criteria: str = 'native_bee_support') -> Dict[str, Any]:
    """
    Generate plant species recommendations based on bee preferences.
    
    Args:
        dataset_id: ID of the dataset to analyze
        top_n: Number of top recommendations to return
        criteria: Recommendation criteria
        
    Returns:
        Dict containing plant recommendations
    """
    
    task_correlation_id = str(uuid.uuid4())
    correlation_id.set(task_correlation_id)
    
    logger.info(
        "Starting plant recommendation analysis",
        task_id=self.request.id,
        dataset_id=dataset_id,
        top_n=top_n,
        criteria=criteria,
        correlation_id=task_correlation_id,
        operation="celery_plant_recommendations"
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
        
        # Use DuckDB for efficient analysis
        with DuckDBService() as duckdb_service:
            # Load data into DuckDB
            table_name = f"dataset_{dataset_id}_{int(time.time())}"
            duckdb_service.load_csv_direct(dataset.file_path, table_name)
            
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'status': 'Analyzing plant preferences',
                    'correlation_id': task_correlation_id,
                    'progress': 50
                }
            )
            
            # Get plant recommendations using DuckDB
            recommendations = duckdb_service.get_plant_recommendations(table_name, top_n)
            
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'status': 'Generating final results',
                    'correlation_id': task_correlation_id,
                    'progress': 80
                }
            )
            
            # Analyze bee preferences for context
            bee_analysis = duckdb_service.analyze_bee_preferences(table_name)
            
            # Prepare results
            results = {
                'recommendations': recommendations,
                'bee_analysis_summary': bee_analysis['summary'],
                'criteria_used': criteria,
                'total_plants_analyzed': len(recommendations),
                'analysis_criteria': {
                    'bee_count_weight': 0.4,
                    'avg_bees_weight': 0.3,
                    'native_bee_ratio_weight': 0.3
                },
                'correlation_id': task_correlation_id
            }
            
            # Update job status
            db_service.update_job_status(
                self.request.id, 
                'completed', 
                results,
                celery_task_id=self.request.id
            )
            
            logger.info(
                "Plant recommendations generated successfully",
                task_id=self.request.id,
                dataset_id=dataset_id,
                recommendations_count=len(recommendations),
                correlation_id=task_correlation_id,
                operation="celery_plant_recommendations"
            )
            
            return results
            
    except Exception as e:
        logger.error(
            "Plant recommendation analysis failed",
            task_id=self.request.id,
            dataset_id=dataset_id,
            error=str(e),
            correlation_id=task_correlation_id,
            operation="celery_plant_recommendations"
        )
        
        if db:
            db_service.update_job_status(
                self.request.id, 
                'failed', 
                {'error': str(e), 'correlation_id': task_correlation_id},
                celery_task_id=self.request.id
            )
        
        raise
    finally:
        if db:
            db.close()
        correlation_id.set(None)


@celery_app.task(bind=True, name='pollinexus.tasks.analysis.seasonal_analysis')
@monitor_performance("celery_seasonal_analysis")
@track_errors("celery_analysis")
def seasonal_analysis(self, dataset_id: int, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Perform seasonal analysis of bee activity patterns.
    
    Args:
        dataset_id: ID of the dataset to analyze
        parameters: Analysis parameters
        
    Returns:
        Dict containing seasonal analysis results
    """
    
    task_correlation_id = str(uuid.uuid4())
    correlation_id.set(task_correlation_id)
    
    logger.info(
        "Starting seasonal analysis",
        task_id=self.request.id,
        dataset_id=dataset_id,
        parameters=parameters,
        correlation_id=task_correlation_id,
        operation="celery_seasonal_analysis"
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
                'status': 'Analyzing seasonal patterns',
                'correlation_id': task_correlation_id,
                'progress': 50
            }
        )
        
        # Seasonal analysis
        seasonal_stats = cleaned_data.groupby('season').agg({
            'bees_num': ['count', 'sum', 'mean', 'std'],
            'bee_species': 'nunique',
            'plant_species': 'nunique',
            'nonnative_bee': 'mean'
        }).round(3)
        
        # Flatten column names
        seasonal_stats.columns = ['_'.join(col).strip() for col in seasonal_stats.columns]
        seasonal_stats = seasonal_stats.reset_index()
        
        # Calculate seasonal trends
        seasonal_trends = {}
        for season in cleaned_data['season'].unique():
            season_data = cleaned_data[cleaned_data['season'] == season]
            seasonal_trends[season] = {
                'total_bees': int(season_data['bees_num'].sum()),
                'avg_bees_per_observation': float(season_data['bees_num'].mean()),
                'unique_bee_species': int(season_data['bee_species'].nunique()),
                'unique_plant_species': int(season_data['plant_species'].nunique()),
                'native_bee_ratio': float(1 - season_data['nonnative_bee'].mean()),
                'observation_count': int(len(season_data))
            }
        
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Generating results',
                'correlation_id': task_correlation_id,
                'progress': 80
            }
        )
        
        # Prepare results
        results = {
            'seasonal_statistics': seasonal_stats.to_dict('records'),
            'seasonal_trends': seasonal_trends,
            'peak_season': max(seasonal_trends.items(), key=lambda x: x[1]['total_bees'])[0],
            'lowest_season': min(seasonal_trends.items(), key=lambda x: x[1]['total_bees'])[0],
            'total_observations': len(cleaned_data),
            'seasons_analyzed': list(seasonal_trends.keys()),
            'parameters': parameters or {},
            'correlation_id': task_correlation_id
        }
        
        # Update job status
        db_service.update_job_status(
            self.request.id, 
            'completed', 
            results,
            celery_task_id=self.request.id
        )
        
        logger.info(
            "Seasonal analysis completed successfully",
            task_id=self.request.id,
            dataset_id=dataset_id,
            peak_season=results['peak_season'],
            total_observations=results['total_observations'],
            correlation_id=task_correlation_id,
            operation="celery_seasonal_analysis"
        )
        
        return results
        
    except Exception as e:
        logger.error(
            "Seasonal analysis failed",
            task_id=self.request.id,
            dataset_id=dataset_id,
            error=str(e),
            correlation_id=task_correlation_id,
            operation="celery_seasonal_analysis"
        )
        
        if db:
            db_service.update_job_status(
                self.request.id, 
                'failed', 
                {'error': str(e), 'correlation_id': task_correlation_id},
                celery_task_id=self.request.id
            )
        
        raise
    finally:
        if db:
            db.close()
        correlation_id.set(None)


@celery_app.task(bind=True, name='pollinexus.tasks.analysis.site_comparison')
@monitor_performance("celery_site_comparison")
@track_errors("celery_analysis")
def site_comparison(self, dataset_id: int, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Compare bee activity across different sites.
    
    Args:
        dataset_id: ID of the dataset to analyze
        parameters: Analysis parameters
        
    Returns:
        Dict containing site comparison results
    """
    
    task_correlation_id = str(uuid.uuid4())
    correlation_id.set(task_correlation_id)
    
    logger.info(
        "Starting site comparison analysis",
        task_id=self.request.id,
        dataset_id=dataset_id,
        parameters=parameters,
        correlation_id=task_correlation_id,
        operation="celery_site_comparison"
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
        
        # Use DuckDB for efficient analysis
        with DuckDBService() as duckdb_service:
            table_name = f"dataset_{dataset_id}_{int(time.time())}"
            duckdb_service.load_csv_direct(dataset.file_path, table_name)
            
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'status': 'Analyzing site patterns',
                    'correlation_id': task_correlation_id,
                    'progress': 50
                }
            )
            
            # Get site analysis
            site_analysis = duckdb_service.analyze_bee_preferences(table_name)
            
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'status': 'Generating comparison results',
                    'correlation_id': task_correlation_id,
                    'progress': 80
                }
            )
            
            # Prepare results
            results = {
                'site_analysis': site_analysis['site_analysis'],
                'site_rankings': {
                    'by_total_bees': sorted(
                        site_analysis['site_analysis'], 
                        key=lambda x: x['total_bees'], 
                        reverse=True
                    ),
                    'by_bee_diversity': sorted(
                        site_analysis['site_analysis'], 
                        key=lambda x: x['unique_bee_species'], 
                        reverse=True
                    ),
                    'by_plant_diversity': sorted(
                        site_analysis['site_analysis'], 
                        key=lambda x: x['unique_plant_species'], 
                        reverse=True
                    )
                },
                'summary': {
                    'total_sites': len(site_analysis['site_analysis']),
                    'most_active_site': max(site_analysis['site_analysis'], key=lambda x: x['total_bees'])['site'],
                    'most_diverse_site': max(site_analysis['site_analysis'], key=lambda x: x['unique_bee_species'])['site']
                },
                'parameters': parameters or {},
                'correlation_id': task_correlation_id
            }
            
            # Update job status
            db_service.update_job_status(
                self.request.id, 
                'completed', 
                results,
                celery_task_id=self.request.id
            )
            
            logger.info(
                "Site comparison completed successfully",
                task_id=self.request.id,
                dataset_id=dataset_id,
                total_sites=results['summary']['total_sites'],
                most_active_site=results['summary']['most_active_site'],
                correlation_id=task_correlation_id,
                operation="celery_site_comparison"
            )
            
            return results
            
    except Exception as e:
        logger.error(
            "Site comparison failed",
            task_id=self.request.id,
            dataset_id=dataset_id,
            error=str(e),
            correlation_id=task_correlation_id,
            operation="celery_site_comparison"
        )
        
        if db:
            db_service.update_job_status(
                self.request.id, 
                'failed', 
                {'error': str(e), 'correlation_id': task_correlation_id},
                celery_task_id=self.request.id
            )
        
        raise
    finally:
        if db:
            db.close()
        correlation_id.set(None) 