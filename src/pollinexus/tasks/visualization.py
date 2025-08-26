"""
Visualization tasks for Pollinexus.

This module contains Celery tasks for data visualization operations
with comprehensive logging and monitoring.
"""

from celery import current_task
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import time
import uuid
import os
from pathlib import Path

from ..services.data_service import DataService
from ..services.database_service import DatabaseService
from ..services.duckdb_service import DuckDBService
from ..core.database import SessionLocal
from ..core.logging import logger, correlation_id
from ..core.metrics import monitor_performance
from ..core.error_tracking import track_errors, error_tracker
from .celery_app import celery_app

# Set matplotlib backend for non-interactive use
plt.switch_backend('Agg')

# Create output directory for visualizations
VISUALIZATION_DIR = Path("visualizations")
VISUALIZATION_DIR.mkdir(exist_ok=True)


@celery_app.task(bind=True, name='pollinexus.tasks.visualization.create_bee_distribution_plot')
@monitor_performance("celery_bee_distribution_plot")
@track_errors("celery_visualization")
def create_bee_distribution_plot(self, dataset_id: int, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create bee species distribution visualization.
    
    Args:
        dataset_id: ID of the dataset to visualize
        parameters: Visualization parameters
        
    Returns:
        Dict containing plot data and metadata
    """
    
    task_correlation_id = str(uuid.uuid4())
    correlation_id.set(task_correlation_id)
    
    logger.info(
        "Starting bee distribution plot creation",
        task_id=self.request.id,
        dataset_id=dataset_id,
        parameters=parameters,
        correlation_id=task_correlation_id,
        operation="celery_bee_distribution_plot"
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
                'status': 'Creating visualization',
                'correlation_id': task_correlation_id,
                'progress': 50
            }
        )
        
        # Create bee species distribution plot
        bee_counts = cleaned_data['bee_species'].value_counts().head(20)
        
        # Create Plotly figure
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=bee_counts.values,
            y=bee_counts.index,
            orientation='h',
            marker_color='lightblue',
            name='Bee Species Count'
        ))
        
        fig.update_layout(
            title='Top 20 Bee Species Distribution',
            xaxis_title='Number of Observations',
            yaxis_title='Bee Species',
            height=600,
            showlegend=False
        )
        
        # Save plot
        plot_filename = f"bee_distribution_{dataset_id}_{int(time.time())}.html"
        plot_path = VISUALIZATION_DIR / plot_filename
        fig.write_html(str(plot_path))
        
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
            'plot_type': 'bee_distribution',
            'plot_path': str(plot_path),
            'plot_filename': plot_filename,
            'plot_data': {
                'bee_species': bee_counts.index.tolist(),
                'counts': bee_counts.values.tolist(),
                'total_species': len(cleaned_data['bee_species'].unique()),
                'total_observations': len(cleaned_data)
            },
            'parameters': parameters or {},
            'correlation_id': task_correlation_id
        }
        
        logger.info(
            "Bee distribution plot created successfully",
            task_id=self.request.id,
            dataset_id=dataset_id,
            plot_path=str(plot_path),
            total_species=results['plot_data']['total_species'],
            correlation_id=task_correlation_id,
            operation="celery_bee_distribution_plot"
        )
        
        return results
        
    except Exception as e:
        logger.error(
            "Bee distribution plot creation failed",
            task_id=self.request.id,
            dataset_id=dataset_id,
            error=str(e),
            correlation_id=task_correlation_id,
            operation="celery_bee_distribution_plot"
        )
        raise
    finally:
        if db:
            db.close()
        correlation_id.set(None)


@celery_app.task(bind=True, name='pollinexus.tasks.visualization.create_seasonal_patterns_plot')
@monitor_performance("celery_seasonal_patterns_plot")
@track_errors("celery_visualization")
def create_seasonal_patterns_plot(self, dataset_id: int, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create seasonal patterns visualization.
    
    Args:
        dataset_id: ID of the dataset to visualize
        parameters: Visualization parameters
        
    Returns:
        Dict containing plot data and metadata
    """
    
    task_correlation_id = str(uuid.uuid4())
    correlation_id.set(task_correlation_id)
    
    logger.info(
        "Starting seasonal patterns plot creation",
        task_id=self.request.id,
        dataset_id=dataset_id,
        parameters=parameters,
        correlation_id=task_correlation_id,
        operation="celery_seasonal_patterns_plot"
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
                'status': 'Creating visualization',
                'correlation_id': task_correlation_id,
                'progress': 50
            }
        )
        
        # Create seasonal patterns plot
        seasonal_data = cleaned_data.groupby('season').agg({
            'bees_num': ['sum', 'mean', 'count'],
            'bee_species': 'nunique',
            'plant_species': 'nunique'
        }).round(2)
        
        seasonal_data.columns = ['total_bees', 'avg_bees', 'observations', 'bee_species', 'plant_species']
        seasonal_data = seasonal_data.reset_index()
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Total Bees by Season', 'Average Bees by Season', 
                          'Bee Species Diversity', 'Plant Species Diversity'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Total bees
        fig.add_trace(
            go.Bar(x=seasonal_data['season'], y=seasonal_data['total_bees'], 
                   name='Total Bees', marker_color='lightcoral'),
            row=1, col=1
        )
        
        # Average bees
        fig.add_trace(
            go.Bar(x=seasonal_data['season'], y=seasonal_data['avg_bees'], 
                   name='Average Bees', marker_color='lightgreen'),
            row=1, col=2
        )
        
        # Bee species diversity
        fig.add_trace(
            go.Bar(x=seasonal_data['season'], y=seasonal_data['bee_species'], 
                   name='Bee Species', marker_color='lightblue'),
            row=2, col=1
        )
        
        # Plant species diversity
        fig.add_trace(
            go.Bar(x=seasonal_data['season'], y=seasonal_data['plant_species'], 
                   name='Plant Species', marker_color='lightyellow'),
            row=2, col=2
        )
        
        fig.update_layout(
            title='Seasonal Patterns Analysis',
            height=800,
            showlegend=False
        )
        
        # Save plot
        plot_filename = f"seasonal_patterns_{dataset_id}_{int(time.time())}.html"
        plot_path = VISUALIZATION_DIR / plot_filename
        fig.write_html(str(plot_path))
        
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
            'plot_type': 'seasonal_patterns',
            'plot_path': str(plot_path),
            'plot_filename': plot_filename,
            'plot_data': seasonal_data.to_dict('records'),
            'parameters': parameters or {},
            'correlation_id': task_correlation_id
        }
        
        logger.info(
            "Seasonal patterns plot created successfully",
            task_id=self.request.id,
            dataset_id=dataset_id,
            plot_path=str(plot_path),
            seasons_analyzed=len(seasonal_data),
            correlation_id=task_correlation_id,
            operation="celery_seasonal_patterns_plot"
        )
        
        return results
        
    except Exception as e:
        logger.error(
            "Seasonal patterns plot creation failed",
            task_id=self.request.id,
            dataset_id=dataset_id,
            error=str(e),
            correlation_id=task_correlation_id,
            operation="celery_seasonal_patterns_plot"
        )
        raise
    finally:
        if db:
            db.close()
        correlation_id.set(None)


@celery_app.task(bind=True, name='pollinexus.tasks.visualization.create_site_comparison_plot')
@monitor_performance("celery_site_comparison_plot")
@track_errors("celery_visualization")
def create_site_comparison_plot(self, dataset_id: int, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create site comparison visualization.
    
    Args:
        dataset_id: ID of the dataset to visualize
        parameters: Visualization parameters
        
    Returns:
        Dict containing plot data and metadata
    """
    
    task_correlation_id = str(uuid.uuid4())
    correlation_id.set(task_correlation_id)
    
    logger.info(
        "Starting site comparison plot creation",
        task_id=self.request.id,
        dataset_id=dataset_id,
        parameters=parameters,
        correlation_id=task_correlation_id,
        operation="celery_site_comparison_plot"
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
                    'status': 'Analyzing site data',
                    'correlation_id': task_correlation_id,
                    'progress': 40
                }
            )
            
            # Get site analysis
            site_analysis = duckdb_service.analyze_bee_preferences(table_name)
            site_data = site_analysis['site_analysis']
            
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'status': 'Creating visualization',
                    'correlation_id': task_correlation_id,
                    'progress': 60
                }
            )
            
            # Create site comparison plot
            sites = [site['site'] for site in site_data]
            total_bees = [site['total_bees'] for site in site_data]
            bee_species = [site['unique_bee_species'] for site in site_data]
            plant_species = [site['unique_plant_species'] for site in site_data]
            
            # Create subplots
            fig = make_subplots(
                rows=1, cols=3,
                subplot_titles=('Total Bees by Site', 'Bee Species Diversity', 'Plant Species Diversity'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Total bees
            fig.add_trace(
                go.Bar(x=sites, y=total_bees, name='Total Bees', marker_color='lightcoral'),
                row=1, col=1
            )
            
            # Bee species diversity
            fig.add_trace(
                go.Bar(x=sites, y=bee_species, name='Bee Species', marker_color='lightblue'),
                row=1, col=2
            )
            
            # Plant species diversity
            fig.add_trace(
                go.Bar(x=sites, y=plant_species, name='Plant Species', marker_color='lightgreen'),
                row=1, col=3
            )
            
            fig.update_layout(
                title='Site Comparison Analysis',
                height=500,
                showlegend=False
            )
            
            # Save plot
            plot_filename = f"site_comparison_{dataset_id}_{int(time.time())}.html"
            plot_path = VISUALIZATION_DIR / plot_filename
            fig.write_html(str(plot_path))
            
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
                'plot_type': 'site_comparison',
                'plot_path': str(plot_path),
                'plot_filename': plot_filename,
                'plot_data': site_data,
                'parameters': parameters or {},
                'correlation_id': task_correlation_id
            }
            
            logger.info(
                "Site comparison plot created successfully",
                task_id=self.request.id,
                dataset_id=dataset_id,
                plot_path=str(plot_path),
                sites_analyzed=len(site_data),
                correlation_id=task_correlation_id,
                operation="celery_site_comparison_plot"
            )
            
            return results
            
    except Exception as e:
        logger.error(
            "Site comparison plot creation failed",
            task_id=self.request.id,
            dataset_id=dataset_id,
            error=str(e),
            correlation_id=task_correlation_id,
            operation="celery_site_comparison_plot"
        )
        raise
    finally:
        if db:
            db.close()
        correlation_id.set(None)


@celery_app.task(bind=True, name='pollinexus.tasks.visualization.create_interactive_dashboard')
@monitor_performance("celery_interactive_dashboard")
@track_errors("celery_visualization")
def create_interactive_dashboard(self, dataset_id: int, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create comprehensive interactive dashboard.
    
    Args:
        dataset_id: ID of the dataset to visualize
        parameters: Visualization parameters
        
    Returns:
        Dict containing dashboard data and metadata
    """
    
    task_correlation_id = str(uuid.uuid4())
    correlation_id.set(task_correlation_id)
    
    logger.info(
        "Starting interactive dashboard creation",
        task_id=self.request.id,
        dataset_id=dataset_id,
        parameters=parameters,
        correlation_id=task_correlation_id,
        operation="celery_interactive_dashboard"
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
        
        # Load and clean data
        data_service = DataService()
        data = data_service.load_dataset(dataset.file_path)
        cleaned_data = data_service.clean_dataset(data)
        
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Creating dashboard components',
                'correlation_id': task_correlation_id,
                'progress': 30
            }
        )
        
        # Create comprehensive dashboard
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Bee Species Distribution', 'Seasonal Bee Activity',
                'Site Comparison', 'Plant-Bee Relationships',
                'Native vs Non-native Bees', 'Observation Timeline'
            ),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 1. Bee species distribution
        bee_counts = cleaned_data['bee_species'].value_counts().head(10)
        fig.add_trace(
            go.Bar(x=bee_counts.values, y=bee_counts.index, orientation='h', 
                   name='Bee Species', marker_color='lightblue'),
            row=1, col=1
        )
        
        # 2. Seasonal bee activity
        seasonal_bees = cleaned_data.groupby('season')['bees_num'].sum()
        fig.add_trace(
            go.Bar(x=seasonal_bees.index, y=seasonal_bees.values, 
                   name='Seasonal Activity', marker_color='lightcoral'),
            row=1, col=2
        )
        
        # 3. Site comparison
        site_bees = cleaned_data.groupby('site')['bees_num'].sum()
        fig.add_trace(
            go.Bar(x=site_bees.index, y=site_bees.values, 
                   name='Site Activity', marker_color='lightgreen'),
            row=2, col=1
        )
        
        # 4. Plant-bee relationships
        plant_bees = cleaned_data.groupby('plant_species')['bees_num'].sum().head(10)
        fig.add_trace(
            go.Bar(x=plant_bees.index, y=plant_bees.values, 
                   name='Plant Activity', marker_color='lightyellow'),
            row=2, col=2
        )
        
        # 5. Native vs non-native bees
        native_ratio = cleaned_data.groupby('season')['nonnative_bee'].mean()
        fig.add_trace(
            go.Bar(x=native_ratio.index, y=1-native_ratio.values, 
                   name='Native Bee Ratio', marker_color='lightpink'),
            row=3, col=1
        )
        
        # 6. Observation timeline (if date column exists)
        if 'date' in cleaned_data.columns:
            timeline_data = cleaned_data.groupby(cleaned_data['date'].dt.date)['bees_num'].sum()
            fig.add_trace(
                go.Scatter(x=timeline_data.index, y=timeline_data.values, 
                          mode='lines+markers', name='Timeline', line_color='lightseagreen'),
                row=3, col=2
            )
        
        fig.update_layout(
            title=f'Pollinexus Dashboard - Dataset {dataset_id}',
            height=1200,
            showlegend=False
        )
        
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Saving dashboard',
                'correlation_id': task_correlation_id,
                'progress': 70
            }
        )
        
        # Save dashboard
        dashboard_filename = f"dashboard_{dataset_id}_{int(time.time())}.html"
        dashboard_path = VISUALIZATION_DIR / dashboard_filename
        fig.write_html(str(dashboard_path))
        
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
            'plot_type': 'interactive_dashboard',
            'plot_path': str(dashboard_path),
            'plot_filename': dashboard_filename,
            'dashboard_summary': {
                'total_observations': len(cleaned_data),
                'total_bees': int(cleaned_data['bees_num'].sum()),
                'unique_bee_species': int(cleaned_data['bee_species'].nunique()),
                'unique_plant_species': int(cleaned_data['plant_species'].nunique()),
                'unique_sites': int(cleaned_data['site'].nunique()),
                'seasons_covered': list(cleaned_data['season'].unique())
            },
            'parameters': parameters or {},
            'correlation_id': task_correlation_id
        }
        
        logger.info(
            "Interactive dashboard created successfully",
            task_id=self.request.id,
            dataset_id=dataset_id,
            dashboard_path=str(dashboard_path),
            total_observations=results['dashboard_summary']['total_observations'],
            correlation_id=task_correlation_id,
            operation="celery_interactive_dashboard"
        )
        
        return results
        
    except Exception as e:
        logger.error(
            "Interactive dashboard creation failed",
            task_id=self.request.id,
            dataset_id=dataset_id,
            error=str(e),
            correlation_id=task_correlation_id,
            operation="celery_interactive_dashboard"
        )
        raise
    finally:
        if db:
            db.close()
        correlation_id.set(None) 