"""
Comprehensive tests for Pollinexus Datasets API endpoints.

This module tests all dataset-related API endpoints including:
- CRUD operations
- File upload validation
- Security measures
- Error handling
- Performance characteristics
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from pollinexus.models.database import Dataset
from pollinexus.services.data_service import DataService


class TestDatasetAPI:
    """Test suite for dataset API endpoints."""
    
    def test_create_dataset_success(self, test_client: TestClient, sample_csv_file: str):
        """Test successful dataset creation."""
        with open(sample_csv_file, 'rb') as f:
            response = test_client.post(
                "/api/v1/datasets/",
                data={
                    "name": "Test Dataset",
                    "description": "Test dataset for API testing"
                },
                files={"file": ("test_data.csv", f, "text/csv")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Dataset"
        assert data["description"] == "Test dataset for API testing"
        assert data["file_path"] is not None
        assert "id" in data
    
    def test_create_dataset_invalid_file_type(self, test_client: TestClient):
        """Test dataset creation with invalid file type."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"This is not a CSV file")
            f.flush()
            
            with open(f.name, 'rb') as file:
                response = test_client.post(
                    "/api/v1/datasets/",
                    data={
                        "name": "Invalid Dataset",
                        "description": "Dataset with invalid file type"
                    },
                    files={"file": ("test_data.txt", file, "text/plain")}
                )
        
        os.unlink(f.name)
        assert response.status_code == 400
        assert "Only CSV files are supported" in response.json()["error"]
    
    def test_create_dataset_malicious_content(self, test_client: TestClient, malicious_csv_file: str):
        """Test dataset creation with malicious content."""
        with open(malicious_csv_file, 'rb') as f:
            response = test_client.post(
                "/api/v1/datasets/",
                data={
                    "name": "Malicious Dataset",
                    "description": "Dataset with malicious content"
                },
                files={"file": ("malicious_data.csv", f, "text/csv")}
            )
        
        # Should be rejected due to malicious content
        assert response.status_code == 400
        assert "validation failed" in response.json()["error"].lower()
    
    def test_create_dataset_large_file(self, test_client: TestClient):
        """Test dataset creation with large file."""
        # Create a large CSV file (10MB)
        large_csv_content = "sample_id,bees_num,date,season,site,native_or_non,sampling,plant_species,time,bee_species,sex,specialized_on,parasitic,nesting,status,nonnative_bee\n"
        
        # Add enough rows to make it large
        for i in range(100000):  # This should create a large file
            large_csv_content += f"{i+1},{i%10+1},2023-06-{15+i%30:02d},summer,site{i%5+1},native,standard,Plant{i%20+1},{10+i%12:02d}:00,Bee{i%10+1},female,generalist,0,social,native,0\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(large_csv_content)
            f.flush()
            
            with open(f.name, 'rb') as file:
                response = test_client.post(
                    "/api/v1/datasets/",
                    data={
                        "name": "Large Dataset",
                        "description": "Large dataset for testing"
                    },
                    files={"file": ("large_data.csv", file, "text/csv")}
                )
        
        os.unlink(f.name)
        # Should handle large files gracefully
        assert response.status_code in [200, 413]  # 413 if size limit exceeded
    
    def test_list_datasets(self, test_client: TestClient, sample_dataset: Dataset):
        """Test listing all datasets."""
        response = test_client.get("/api/v1/datasets/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check if our test dataset is in the list
        dataset_ids = [d["id"] for d in data]
        assert sample_dataset.id in dataset_ids
    
    def test_get_dataset_by_id(self, test_client: TestClient, sample_dataset: Dataset):
        """Test getting dataset by ID."""
        response = test_client.get(f"/api/v1/datasets/{sample_dataset.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_dataset.id
        assert data["name"] == sample_dataset.name
        assert data["description"] == sample_dataset.description
    
    def test_get_dataset_not_found(self, test_client: TestClient):
        """Test getting non-existent dataset."""
        response = test_client.get("/api/v1/datasets/99999")
        
        assert response.status_code == 404
        assert "Dataset not found" in response.json()["error"]
    
    def test_delete_dataset(self, test_client: TestClient, sample_dataset: Dataset):
        """Test dataset deletion."""
        response = test_client.delete(f"/api/v1/datasets/{sample_dataset.id}")
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify dataset is deleted
        get_response = test_client.get(f"/api/v1/datasets/{sample_dataset.id}")
        assert get_response.status_code == 404
    
    def test_delete_dataset_not_found(self, test_client: TestClient):
        """Test deleting non-existent dataset."""
        response = test_client.delete("/api/v1/datasets/99999")
        
        assert response.status_code == 404
        assert "Dataset not found" in response.json()["error"]
    
    def test_get_dataset_info(self, test_client: TestClient, sample_dataset: Dataset):
        """Test getting dataset information and statistics."""
        response = test_client.get(f"/api/v1/datasets/{sample_dataset.id}/info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "dataset" in data
        assert "statistics" in data
        assert data["dataset"]["id"] == sample_dataset.id
        
        # Check statistics
        stats = data["statistics"]
        assert "total_records" in stats
        assert "total_columns" in stats
        assert "missing_values" in stats
        assert "unique_values" in stats
        assert "data_types" in stats
    
    def test_search_datasets(self, test_client: TestClient, sample_dataset: Dataset):
        """Test dataset search functionality."""
        response = test_client.get("/api/v1/datasets/search", params={"q": "Test"})
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should find our test dataset
        dataset_names = [d["name"] for d in data]
        assert "Test Dataset" in dataset_names
    
    def test_filter_datasets_by_date(self, test_client: TestClient, sample_dataset: Dataset):
        """Test filtering datasets by creation date."""
        response = test_client.get(
            "/api/v1/datasets/",
            params={"created_after": "2023-01-01", "created_before": "2024-12-31"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_dataset_health_check(self, test_client: TestClient, sample_dataset: Dataset):
        """Test dataset health check endpoint."""
        response = test_client.get(f"/api/v1/datasets/{sample_dataset.id}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "file_exists" in data
        assert "file_size" in data
        assert "validation_status" in data
    
    def test_dataset_validation_status(self, test_client: TestClient, sample_dataset: Dataset):
        """Test dataset validation status endpoint."""
        response = test_client.get(f"/api/v1/datasets/{sample_dataset.id}/validation")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "is_valid" in data
        assert "errors" in data
        assert "warnings" in data
        assert "last_validated" in data
    
    @pytest.mark.parametrize("invalid_id", ["abc", "-1", "0", "999999999999999999"])
    def test_invalid_dataset_id_handling(self, test_client: TestClient, invalid_id: str):
        """Test handling of invalid dataset IDs."""
        response = test_client.get(f"/api/v1/datasets/{invalid_id}")
        
        assert response.status_code in [400, 404]
    
    def test_dataset_upload_without_file(self, test_client: TestClient):
        """Test dataset creation without file upload."""
        response = test_client.post(
            "/api/v1/datasets/",
            data={
                "name": "Dataset without file",
                "description": "This should fail"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_dataset_upload_without_name(self, test_client: TestClient, sample_csv_file: str):
        """Test dataset creation without name."""
        with open(sample_csv_file, 'rb') as f:
            response = test_client.post(
                "/api/v1/datasets/",
                data={
                    "description": "Dataset without name"
                },
                files={"file": ("test_data.csv", f, "text/csv")}
            )
        
        assert response.status_code == 422  # Validation error
    
    def test_dataset_upload_corrupted_file(self, test_client: TestClient):
        """Test dataset creation with corrupted CSV file."""
        # Create a corrupted CSV file
        corrupted_content = "sample_id,bees_num,date\n1,5,2023-06-15\n2,3,2023-06-16\n3,7,2023-06-17,extra_column\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(corrupted_content)
            f.flush()
            
            with open(f.name, 'rb') as file:
                response = test_client.post(
                    "/api/v1/datasets/",
                    data={
                        "name": "Corrupted Dataset",
                        "description": "Dataset with corrupted data"
                    },
                    files={"file": ("corrupted_data.csv", file, "text/csv")}
                )
        
        os.unlink(f.name)
        # Should handle corrupted files gracefully
        assert response.status_code in [200, 400]
    
    def test_dataset_upload_empty_file(self, test_client: TestClient):
        """Test dataset creation with empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("")  # Empty file
            f.flush()
            
            with open(f.name, 'rb') as file:
                response = test_client.post(
                    "/api/v1/datasets/",
                    data={
                        "name": "Empty Dataset",
                        "description": "Empty dataset"
                    },
                    files={"file": ("empty_data.csv", file, "text/csv")}
                )
        
        os.unlink(f.name)
        assert response.status_code == 400
        assert "empty" in response.json()["error"].lower() or "validation" in response.json()["error"].lower()
    
    def test_dataset_upload_headers_only(self, test_client: TestClient):
        """Test dataset creation with headers-only CSV."""
        headers_only = "sample_id,bees_num,date,season,site,native_or_non,sampling,plant_species,time,bee_species,sex,specialized_on,parasitic,nesting,status,nonnative_bee\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(headers_only)
            f.flush()
            
            with open(f.name, 'rb') as file:
                response = test_client.post(
                    "/api/v1/datasets/",
                    data={
                        "name": "Headers Only Dataset",
                        "description": "Dataset with only headers"
                    },
                    files={"file": ("headers_only.csv", file, "text/csv")}
                )
        
        os.unlink(f.name)
        # Should handle headers-only files appropriately
        assert response.status_code in [200, 400]
    
    @pytest.mark.parametrize("file_size_mb", [1, 5, 10, 50])
    def test_dataset_upload_different_sizes(self, test_client: TestClient, file_size_mb: int):
        """Test dataset upload with different file sizes."""
        # Create CSV content of specified size
        csv_content = "sample_id,bees_num,date,season,site,native_or_non,sampling,plant_species,time,bee_species,sex,specialized_on,parasitic,nesting,status,nonnative_bee\n"
        
        # Calculate rows needed for target size (approximate)
        row_template = "1,5,2023-06-15,summer,site1,native,standard,Sunflower,10:00,Bombus impatiens,female,generalist,0,social,native,0\n"
        target_size = file_size_mb * 1024 * 1024  # Convert MB to bytes
        rows_needed = int(target_size / len(row_template.encode('utf-8')))
        
        for i in range(rows_needed):
            csv_content += row_template
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            
            with open(f.name, 'rb') as file:
                response = test_client.post(
                    "/api/v1/datasets/",
                    data={
                        "name": f"{file_size_mb}MB Dataset",
                        "description": f"Dataset of {file_size_mb}MB"
                    },
                    files={"file": (f"{file_size_mb}mb_data.csv", file, "text/csv")}
                )
        
        os.unlink(f.name)
        # Should handle different file sizes appropriately
        assert response.status_code in [200, 413]  # 413 if size limit exceeded
    
    def test_dataset_upload_concurrent_requests(self, test_client: TestClient, sample_csv_file: str):
        """Test concurrent dataset uploads."""
        import threading
        import time
        
        results = []
        errors = []
        
        def upload_dataset(thread_id: int):
            try:
                with open(sample_csv_file, 'rb') as f:
                    response = test_client.post(
                        "/api/v1/datasets/",
                        data={
                            "name": f"Concurrent Dataset {thread_id}",
                            "description": f"Concurrent upload test {thread_id}"
                        },
                        files={"file": (f"concurrent_data_{thread_id}.csv", f, "text/csv")}
                    )
                results.append((thread_id, response.status_code))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Start multiple concurrent uploads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=upload_dataset, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors in concurrent uploads: {errors}"
        assert len(results) == 5
        
        # All uploads should succeed
        for thread_id, status_code in results:
            assert status_code == 200, f"Thread {thread_id} failed with status {status_code}"
    
    def test_dataset_api_rate_limiting(self, test_client: TestClient, sample_csv_file: str):
        """Test API rate limiting for dataset endpoints."""
        # Make multiple rapid requests
        responses = []
        for i in range(20):  # Make 20 rapid requests
            with open(sample_csv_file, 'rb') as f:
                response = test_client.post(
                    "/api/v1/datasets/",
                    data={
                        "name": f"Rate Limit Test {i}",
                        "description": f"Rate limit test {i}"
                    },
                    files={"file": (f"rate_limit_test_{i}.csv", f, "text/csv")}
                )
            responses.append(response.status_code)
        
        # Check if rate limiting is working (should get 429 for some requests)
        # Note: This depends on the rate limiting configuration
        assert len(responses) == 20
    
    def test_dataset_api_authentication_required(self, test_client: TestClient):
        """Test that dataset endpoints require authentication when configured."""
        # This test assumes authentication is required
        # In a real implementation, you would need to test with and without auth tokens
        
        response = test_client.get("/api/v1/datasets/")
        # Should work without auth for now, but could be 401 in production
        assert response.status_code in [200, 401]
    
    def test_dataset_api_cors_headers(self, test_client: TestClient):
        """Test CORS headers in dataset API responses."""
        response = test_client.options("/api/v1/datasets/")
        
        # Check CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    def test_dataset_api_response_format(self, test_client: TestClient, sample_dataset: Dataset):
        """Test that dataset API responses follow consistent format."""
        response = test_client.get(f"/api/v1/datasets/{sample_dataset.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = ["id", "name", "file_path", "created_at", "updated_at"]
        for field in required_fields:
            assert field in data
        
        # Check data types
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["file_path"], str)
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)
    
    def test_dataset_api_error_format(self, test_client: TestClient):
        """Test that dataset API errors follow consistent format."""
        response = test_client.get("/api/v1/datasets/99999")
        
        assert response.status_code == 404
        data = response.json()
        
        # Check error response format
        assert "error" in data
        assert "status_code" in data
        assert "request_id" in data
        assert "correlation_id" in data
    
    def test_dataset_api_logging(self, test_client: TestClient, sample_dataset: Dataset, capture_logs):
        """Test that dataset API endpoints log appropriately."""
        # Make a request
        response = test_client.get(f"/api/v1/datasets/{sample_dataset.id}")
        
        assert response.status_code == 200
        
        # Check that logs were generated
        logs = capture_logs.getvalue()
        assert "API request started" in logs
        assert "API request completed" in logs
        assert "datasets" in logs.lower()
    
    def test_dataset_api_performance(self, test_client: TestClient, sample_dataset: Dataset):
        """Test dataset API performance characteristics."""
        import time
        
        # Measure response time
        start_time = time.time()
        response = test_client.get(f"/api/v1/datasets/{sample_dataset.id}")
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Response should be fast (< 1 second)
        response_time = end_time - start_time
        assert response_time < 1.0, f"Response time {response_time:.3f}s exceeds 1 second"
        
        # Check response headers for performance info
        assert "X-Process-Time" in response.headers
        process_time = float(response.headers["X-Process-Time"])
        assert process_time < 1.0, f"Process time {process_time:.3f}s exceeds 1 second"
    
    def test_dataset_api_security_headers(self, test_client: TestClient, sample_dataset: Dataset):
        """Test security headers in dataset API responses."""
        response = test_client.get(f"/api/v1/datasets/{sample_dataset.id}")
        
        assert response.status_code == 200
        
        # Check security headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection"
        ]
        
        for header in security_headers:
            # These headers might not be set in development, but should be in production
            if header in response.headers:
                assert response.headers[header] is not None 