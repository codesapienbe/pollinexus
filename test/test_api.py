"""
Comprehensive API testing suite for Pollinexus API.

This module contains tests for all API endpoints including
dataset management, analysis operations, and visualizations.
"""

import pytest
import tempfile
import os
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pollinexus.api.main import app
from pollinexus.core.database import get_db
from pollinexus.models.database import Base
from pollinexus.services.database_service import DatabaseService
from pollinexus.services.data_service import DataService


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    """Create database session for testing."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_csv_file():
    """Create a sample CSV file for testing."""
    csv_content = """sample_id,bees_num,date,season,site,native_or_non,sampling,plant_species,time,bee_species,sex,specialized_on,parasitic,nesting,status,nonnative_bee
1,5,2023-06-15,early,site1,native,hand,species1,10:00,Apis mellifera,M,genus1,0,ground,native,0
2,3,2023-06-15,early,site1,native,hand,species2,10:30,Bombus terrestris,F,genus2,0,ground,native,0
3,7,2023-06-15,early,site2,non-native,hand,species3,11:00,Apis mellifera,M,genus1,0,ground,non-native,1"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


class TestHealthEndpoints:
    """Test health and monitoring endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
        assert "request_id" in data
        assert "correlation_id" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Welcome to Pollinexus API"
        assert "version" in data
        assert "documentation" in data
    
    def test_api_info(self, client):
        """Test API info endpoint."""
        response = client.get("/api/v1/info")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Pollinexus API"
        assert "endpoints" in data
        assert "features" in data
        assert "documentation" in data
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data


class TestDatasetEndpoints:
    """Test dataset management endpoints."""
    
    def test_create_dataset(self, client, sample_csv_file):
        """Test dataset creation."""
        with open(sample_csv_file, 'rb') as f:
            response = client.post(
                "/api/v1/datasets/",
                files={"file": ("test.csv", f, "text/csv")},
                data={
                    "name": "Test Dataset",
                    "description": "Test dataset for API testing"
                }
            )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Test Dataset"
        assert data["description"] == "Test dataset for API testing"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_dataset_invalid_file(self, client):
        """Test dataset creation with invalid file."""
        response = client.post(
            "/api/v1/datasets/",
            files={"file": ("test.txt", b"invalid content", "text/plain")},
            data={
                "name": "Test Dataset",
                "description": "Test dataset"
            }
        )
        
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]
    
    def test_list_datasets(self, client, db_session):
        """Test dataset listing."""
        # Create a test dataset first
        db_service = DatabaseService(db_session)
        dataset_create = Mock()
        dataset_create.name = "Test Dataset"
        dataset_create.description = "Test description"
        dataset_create.file_path = "test/path.csv"
        
        db_service.create_dataset(dataset_create)
        
        response = client.get("/api/v1/datasets/")
        assert response.status_code == 200
        
        data = response.json()
        assert "datasets" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
    
    def test_get_dataset(self, client, db_session):
        """Test get dataset by ID."""
        # Create a test dataset first
        db_service = DatabaseService(db_session)
        dataset_create = Mock()
        dataset_create.name = "Test Dataset"
        dataset_create.description = "Test description"
        dataset_create.file_path = "test/path.csv"
        
        dataset = db_service.create_dataset(dataset_create)
        
        response = client.get(f"/api/v1/datasets/{dataset.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Test Dataset"
        assert data["id"] == dataset.id
    
    def test_get_dataset_not_found(self, client):
        """Test get dataset with non-existent ID."""
        response = client.get("/api/v1/datasets/999")
        assert response.status_code == 404
    
    def test_update_dataset(self, client, db_session):
        """Test dataset update."""
        # Create a test dataset first
        db_service = DatabaseService(db_session)
        dataset_create = Mock()
        dataset_create.name = "Test Dataset"
        dataset_create.description = "Test description"
        dataset_create.file_path = "test/path.csv"
        
        dataset = db_service.create_dataset(dataset_create)
        
        update_data = {
            "name": "Updated Dataset",
            "description": "Updated description"
        }
        
        response = client.put(f"/api/v1/datasets/{dataset.id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Updated Dataset"
        assert data["description"] == "Updated description"
    
    def test_delete_dataset(self, client, db_session):
        """Test dataset deletion."""
        # Create a test dataset first
        db_service = DatabaseService(db_session)
        dataset_create = Mock()
        dataset_create.name = "Test Dataset"
        dataset_create.description = "Test description"
        dataset_create.file_path = "test/path.csv"
        
        dataset = db_service.create_dataset(dataset_create)
        
        response = client.delete(f"/api/v1/datasets/{dataset.id}")
        assert response.status_code == 200
        
        # Verify dataset is deleted
        response = client.get(f"/api/v1/datasets/{dataset.id}")
        assert response.status_code == 404
    
    def test_dataset_health_check(self, client, db_session):
        """Test dataset health check."""
        # Create a test dataset first
        db_service = DatabaseService(db_session)
        dataset_create = Mock()
        dataset_create.name = "Test Dataset"
        dataset_create.description = "Test description"
        dataset_create.file_path = "test/path.csv"
        
        dataset = db_service.create_dataset(dataset_create)
        
        response = client.get(f"/api/v1/datasets/{dataset.id}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "health_status" in data
        assert "file_status" in data
        assert "validation_status" in data
    
    def test_search_datasets(self, client, db_session):
        """Test dataset search."""
        # Create test datasets first
        db_service = DatabaseService(db_session)
        
        for i in range(3):
            dataset_create = Mock()
            dataset_create.name = f"Test Dataset {i}"
            dataset_create.description = f"Test description {i}"
            dataset_create.file_path = f"test/path_{i}.csv"
            db_service.create_dataset(dataset_create)
        
        search_data = {
            "query": "Test",
            "limit": 10,
            "offset": 0
        }
        
        response = client.post("/api/v1/datasets/search", json=search_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert len(data["results"]) > 0


class TestAnalysisEndpoints:
    """Test analysis endpoints."""
    
    def test_bee_preference_analysis(self, client, db_session):
        """Test bee preference analysis."""
        # Create a test dataset first
        db_service = DatabaseService(db_session)
        dataset_create = Mock()
        dataset_create.name = "Test Dataset"
        dataset_create.description = "Test description"
        dataset_create.file_path = "test/path.csv"
        
        dataset = db_service.create_dataset(dataset_create)
        
        analysis_data = {
            "dataset_id": dataset.id,
            "target_column": "nonnative_bee",
            "model_type": "random_forest",
            "test_size": 0.2
        }
        
        with patch('pollinexus.tasks.analysis.analyze_bee_preferences.delay') as mock_task:
            mock_task.return_value = Mock(id="test-task-id")
            
            response = client.post(
                "/api/v1/analysis/bee-preferences/",
                json=analysis_data
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["dataset_id"] == dataset.id
            assert data["job_type"] == "bee_preferences"
            assert data["status"] == "running"
    
    def test_plant_recommendations(self, client, db_session):
        """Test plant recommendations analysis."""
        # Create a test dataset first
        db_service = DatabaseService(db_session)
        dataset_create = Mock()
        dataset_create.name = "Test Dataset"
        dataset_create.description = "Test description"
        dataset_create.file_path = "test/path.csv"
        
        dataset = db_service.create_dataset(dataset_create)
        
        analysis_data = {
            "dataset_id": dataset.id,
            "top_n": 10,
            "criteria": ["bee_attraction", "seasonal_availability"]
        }
        
        with patch('pollinexus.tasks.analysis.generate_plant_recommendations.delay') as mock_task:
            mock_task.return_value = Mock(id="test-task-id")
            
            response = client.post(
                "/api/v1/analysis/plant-recommendations/",
                json=analysis_data
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["dataset_id"] == dataset.id
            assert data["job_type"] == "plant_recommendations"
    
    def test_analysis_job_status(self, client, db_session):
        """Test analysis job status."""
        # Create a test analysis job first
        db_service = DatabaseService(db_session)
        job_create = Mock()
        job_create.dataset_id = 1
        job_create.job_type = "bee_preferences"
        job_create.parameters = {"test": "params"}
        
        job = db_service.create_analysis_job(job_create)
        
        response = client.get(f"/api/v1/analysis/jobs/{job.id}/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["job_id"] == job.id
        assert data["job_type"] == "bee_preferences"
        assert "status" in data
    
    def test_analysis_results(self, client, db_session):
        """Test analysis results retrieval."""
        # Create a completed analysis job first
        db_service = DatabaseService(db_session)
        job_create = Mock()
        job_create.dataset_id = 1
        job_create.job_type = "bee_preferences"
        job_create.parameters = {"test": "params"}
        
        job = db_service.create_analysis_job(job_create)
        
        # Update job to completed status
        db_service.update_job_status(job.id, "completed", {"results": {"test": "results"}})
        
        response = client.get(f"/api/v1/analysis/jobs/{job.id}/results")
        assert response.status_code == 200
        
        data = response.json()
        assert data["job_id"] == job.id
        assert data["status"] == "completed"
        assert "results" in data
    
    def test_list_analysis_jobs(self, client, db_session):
        """Test analysis jobs listing."""
        # Create test analysis jobs first
        db_service = DatabaseService(db_session)
        
        for i in range(3):
            job_create = Mock()
            job_create.dataset_id = 1
            job_create.job_type = "bee_preferences"
            job_create.parameters = {"test": f"params_{i}"}
            db_service.create_analysis_job(job_create)
        
        response = client.get("/api/v1/analysis/jobs/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 3
    
    def test_cancel_analysis_job(self, client, db_session):
        """Test analysis job cancellation."""
        # Create a running analysis job first
        db_service = DatabaseService(db_session)
        job_create = Mock()
        job_create.dataset_id = 1
        job_create.job_type = "bee_preferences"
        job_create.parameters = {"test": "params"}
        
        job = db_service.create_analysis_job(job_create)
        db_service.update_job_status(job.id, "running")
        
        response = client.delete(f"/api/v1/analysis/jobs/{job.id}")
        assert response.status_code == 200
        
        # Verify job is cancelled
        response = client.get(f"/api/v1/analysis/jobs/{job.id}/status")
        data = response.json()
        assert data["status"] == "cancelled"


class TestVisualizationEndpoints:
    """Test visualization endpoints."""
    
    def test_create_bee_distribution_plot(self, client, db_session):
        """Test bee distribution plot creation."""
        # Create a test dataset first
        db_service = DatabaseService(db_session)
        dataset_create = Mock()
        dataset_create.name = "Test Dataset"
        dataset_create.description = "Test description"
        dataset_create.file_path = "test/path.csv"
        
        dataset = db_service.create_dataset(dataset_create)
        
        with patch('pollinexus.tasks.visualization.create_bee_distribution_plot.delay') as mock_task:
            mock_task.return_value = Mock(id="test-task-id")
            
            response = client.post(
                f"/api/v1/visualizations/bee-distribution/?dataset_id={dataset.id}",
                json={"top_n": 20, "include_percentages": True}
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["dataset_id"] == dataset.id
            assert data["plot_type"] == "bee_distribution"
            assert "task_id" in data["plot_data"]
    
    def test_create_seasonal_patterns_plot(self, client, db_session):
        """Test seasonal patterns plot creation."""
        # Create a test dataset first
        db_service = DatabaseService(db_session)
        dataset_create = Mock()
        dataset_create.name = "Test Dataset"
        dataset_create.description = "Test description"
        dataset_create.file_path = "test/path.csv"
        
        dataset = db_service.create_dataset(dataset_create)
        
        with patch('pollinexus.tasks.visualization.create_seasonal_patterns_plot.delay') as mock_task:
            mock_task.return_value = Mock(id="test-task-id")
            
            response = client.post(
                f"/api/v1/visualizations/seasonal-patterns/?dataset_id={dataset.id}",
                json={"include_trends": True, "seasonal_periods": 12}
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["plot_type"] == "seasonal_patterns"
    
    def test_batch_visualization(self, client, db_session):
        """Test batch visualization creation."""
        # Create a test dataset first
        db_service = DatabaseService(db_session)
        dataset_create = Mock()
        dataset_create.name = "Test Dataset"
        dataset_create.description = "Test description"
        dataset_create.file_path = "test/path.csv"
        
        dataset = db_service.create_dataset(dataset_create)
        
        batch_data = {
            "dataset_id": dataset.id,
            "plot_types": ["bee_distribution", "seasonal_patterns", "site_comparison"],
            "parameters": {
                "top_n": 20,
                "include_trends": True
            }
        }
        
        with patch('pollinexus.tasks.visualization.create_bee_distribution_plot.delay') as mock_bee:
            with patch('pollinexus.tasks.visualization.create_seasonal_patterns_plot.delay') as mock_seasonal:
                with patch('pollinexus.tasks.visualization.create_site_comparison_plot.delay') as mock_site:
                    mock_bee.return_value = Mock(id="task-1")
                    mock_seasonal.return_value = Mock(id="task-2")
                    mock_site.return_value = Mock(id="task-3")
                    
                    response = client.post(
                        "/api/v1/visualizations/batch/",
                        json=batch_data
                    )
                    
                    assert response.status_code == 200
                    
                    data = response.json()
                    assert len(data) == 3
                    assert all("task_id" in viz["plot_data"] for viz in data)
    
    def test_visualization_status(self, client):
        """Test visualization status check."""
        with patch('pollinexus.tasks.celery_app.get_task_status') as mock_status:
            mock_status.return_value = {
                "status": "SUCCESS",
                "ready": True,
                "successful": True,
                "failed": False,
                "info": {
                    "plot_path": "test/path.html",
                    "plot_filename": "test.html",
                    "plot_type": "bee_distribution"
                }
            }
            
            response = client.get(
                "/api/v1/visualizations/1703123456/status?task_id=test-task-id"
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "SUCCESS"
            assert data["ready"] is True
            assert data["successful"] is True
    
    def test_visualization_download(self, client):
        """Test visualization download info."""
        with patch('pollinexus.tasks.celery_app.celery_app.AsyncResult') as mock_result:
            mock_result.return_value.ready.return_value = True
            mock_result.return_value.failed.return_value = False
            mock_result.return_value.get.return_value = {
                "plot_path": "test/path.html",
                "plot_filename": "test.html",
                "plot_type": "bee_distribution"
            }
            
            response = client.get(
                "/api/v1/visualizations/1703123456/download?task_id=test-task-id"
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert "plot_path" in data
            assert "download_url" in data
    
    def test_available_visualization_types(self, client):
        """Test available visualization types endpoint."""
        response = client.get("/api/v1/visualizations/available-types")
        assert response.status_code == 200
        
        data = response.json()
        assert "visualization_types" in data
        assert "total_types" in data
        assert len(data["visualization_types"]) > 0
        
        # Check for expected visualization types
        types = [viz["type"] for viz in data["visualization_types"]]
        assert "bee_distribution" in types
        assert "seasonal_patterns" in types
        assert "site_comparison" in types
        assert "interactive_dashboard" in types


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_dataset_id(self, client):
        """Test handling of invalid dataset ID."""
        response = client.get("/api/v1/datasets/999")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data or "detail" in data
    
    def test_invalid_analysis_job_id(self, client):
        """Test handling of invalid analysis job ID."""
        response = client.get("/api/v1/analysis/jobs/999")
        assert response.status_code == 404
    
    def test_invalid_visualization_id(self, client):
        """Test handling of invalid visualization ID."""
        response = client.get("/api/v1/visualizations/999/status?task_id=invalid")
        assert response.status_code == 200  # Should handle gracefully
    
    def test_missing_required_fields(self, client):
        """Test handling of missing required fields."""
        response = client.post("/api/v1/analysis/bee-preferences/", json={})
        assert response.status_code == 422  # Validation error
    
    def test_invalid_file_upload(self, client):
        """Test handling of invalid file upload."""
        response = client.post(
            "/api/v1/datasets/",
            files={"file": ("test.txt", b"invalid content", "text/plain")},
            data={"name": "Test"}
        )
        assert response.status_code == 400


class TestPerformanceAndMonitoring:
    """Test performance and monitoring features."""
    
    def test_request_logging(self, client):
        """Test that requests are properly logged."""
        response = client.get("/health")
        assert response.status_code == 200
        
        # Check for correlation headers
        assert "X-Correlation-ID" in response.headers
        assert "X-Request-ID" in response.headers
        assert "X-Process-Time" in response.headers
    
    def test_error_logging(self, client):
        """Test that errors are properly logged."""
        response = client.get("/api/v1/datasets/999")
        assert response.status_code == 404
        
        # Check for correlation headers even in error responses
        assert "X-Correlation-ID" in response.headers
        assert "X-Request-ID" in response.headers
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = client.get("/health")
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0
        assert all(status == 200 for status in results)
        assert len(results) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 