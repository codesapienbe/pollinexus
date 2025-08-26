"""
Test configuration and fixtures for Pollinexus API.

This module provides comprehensive test fixtures for database,
services, API clients, and authentication testing.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from pollinexus.core.config import settings
from pollinexus.core.database import get_db, Base
from pollinexus.api.main import app
from pollinexus.services.database_service import DatabaseService
from pollinexus.services.data_service import DataService
from pollinexus.services.duckdb_service import DuckDBService
from pollinexus.services.user_service import UserService
from pollinexus.models.database import Dataset, AnalysisJob, PlantRecommendation
from pollinexus.models.user import User, UserOTP, UserSession


# Test database configuration
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine."""
    return test_engine


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create test database session."""
    # Create tables
    Base.metadata.create_all(bind=test_db_engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop tables
        Base.metadata.drop_all(bind=test_db_engine)


@pytest.fixture(scope="function")
def test_db(test_db_session) -> Generator[Session, None, None]:
    """Override database dependency for testing."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield test_db_session
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_client(test_db) -> Generator[TestClient, None, None]:
    """Create test client for API testing."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def sample_csv_file() -> Generator[str, None, None]:
    """Create a sample CSV file for testing."""
    csv_content = """sample_id,bees_num,date,season,site,native_or_non,sampling,plant_species,time,bee_species,sex,specialized_on,parasitic,nesting,status,nonnative_bee
1,5,2023-06-15,summer,site1,native,standard,Sunflower,10:00,Bombus impatiens,female,generalist,0,social,native,0
2,3,2023-06-16,summer,site1,native,standard,Rose,11:00,Apis mellifera,female,generalist,0,social,native,0
3,7,2023-06-17,summer,site2,native,standard,Lavender,09:00,Bombus terrestris,female,specialist,0,social,native,0
4,2,2023-06-18,summer,site2,native,standard,Daisy,12:00,Apis mellifera,male,generalist,0,social,native,0
5,4,2023-06-19,summer,site3,native,standard,Clover,10:30,Bombus impatiens,female,generalist,0,social,native,0"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture(scope="function")
def sample_dataset(test_db_session, sample_csv_file) -> Dataset:
    """Create a sample dataset for testing."""
    dataset = Dataset(
        name="Test Dataset",
        description="Test dataset for unit testing",
        file_path=sample_csv_file
    )
    test_db_session.add(dataset)
    test_db_session.commit()
    test_db_session.refresh(dataset)
    return dataset


@pytest.fixture(scope="function")
def sample_analysis_job(test_db_session, sample_dataset) -> AnalysisJob:
    """Create a sample analysis job for testing."""
    job = AnalysisJob(
        dataset_id=sample_dataset.id,
        job_type="bee_preferences",
        status="pending",
        parameters={"test": True}
    )
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)
    return job


@pytest.fixture(scope="function")
def sample_user(test_db_session) -> User:
    """Create a sample user for testing."""
    user = User(
        full_name="Test User",
        email="test@example.com",
        phone="+1234567890",
        is_verified=True,
        role="user"
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def sample_user_otp(test_db_session, sample_user) -> UserOTP:
    """Create a sample user OTP for testing."""
    otp = UserOTP(
        user_id=sample_user.user_id,
        otp_code="123456",
        otp_type="email",
        expires_at="2024-12-31 23:59:59",
        is_used=False
    )
    test_db_session.add(otp)
    test_db_session.commit()
    test_db_session.refresh(otp)
    return otp


@pytest.fixture(scope="function")
def mock_user_service():
    """Mock user service for testing."""
    with patch('pollinexus.services.user_service.UserService') as mock:
        service_instance = Mock()
        mock.return_value = service_instance
        
        # Mock user data
        service_instance.get_user_by_email.return_value = {
            "user_id": "test-user-id",
            "full_name": "Test User",
            "email": "test@example.com",
            "phone": "+1234567890",
            "is_verified": True,
            "role": "user",
            "is_deleted": False
        }
        
        service_instance.create_user.return_value = {
            "user_id": "new-user-id",
            "full_name": "New User",
            "email": "new@example.com",
            "phone": "+1234567890",
            "role": "user"
        }
        
        service_instance.create_otp.return_value = "123456"
        service_instance.verify_otp.return_value = True
        service_instance.send_email_notification.return_value = True
        service_instance.send_whatsapp_notification.return_value = True
        
        yield service_instance


@pytest.fixture(scope="function")
def mock_celery_task():
    """Mock Celery task for testing."""
    with patch('pollinexus.tasks.analysis.analyze_bee_preferences') as mock:
        mock.delay.return_value = Mock(id="test-task-id")
        yield mock


@pytest.fixture(scope="function")
def mock_duckdb_service():
    """Mock DuckDB service for testing."""
    with patch('pollinexus.services.duckdb_service.DuckDBService') as mock:
        service_instance = Mock()
        mock.return_value = service_instance
        
        # Mock analysis results
        service_instance.analyze_bee_preferences.return_value = {
            "bee_species_analysis": [
                {"bee_species": "Bombus impatiens", "total_bees": 12, "observation_count": 3}
            ],
            "plant_species_analysis": [
                {"plant_species": "Sunflower", "total_bees": 5, "observation_count": 1}
            ],
            "summary": {
                "total_observations": 5,
                "total_bees": 21,
                "unique_bee_species": 3,
                "unique_plant_species": 5
            }
        }
        
        service_instance.generate_plant_recommendations.return_value = {
            "recommendations": [
                {
                    "plant_species": "Sunflower",
                    "score": 0.85,
                    "bee_count": 5,
                    "avg_bees": 5.0,
                    "native_bee_ratio": 1.0
                }
            ],
            "total_plants_analyzed": 5
        }
        
        yield service_instance


@pytest.fixture(scope="function")
def authenticated_client(test_client, mock_user_service):
    """Create an authenticated test client."""
    # Mock authentication
    with patch('pollinexus.core.auth.get_current_user') as mock_auth:
        mock_auth.return_value = {
            "user_id": "test-user-id",
            "full_name": "Test User",
            "email": "test@example.com",
            "role": "user"
        }
        yield test_client


@pytest.fixture(scope="function")
def admin_client(test_client, mock_user_service):
    """Create an admin test client."""
    # Mock admin authentication
    with patch('pollinexus.core.auth.get_current_user') as mock_auth:
        mock_auth.return_value = {
            "user_id": "admin-user-id",
            "full_name": "Admin User",
            "email": "admin@example.com",
            "role": "admin"
        }
        yield test_client


@pytest.fixture(scope="function")
def test_upload_dir():
    """Create a temporary upload directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture(scope="function")
def mock_file_upload():
    """Mock file upload for testing."""
    with patch('fastapi.UploadFile') as mock:
        mock_file = Mock()
        mock_file.filename = "test_data.csv"
        mock_file.content_type = "text/csv"
        mock_file.size = 1024
        mock_file.file = Mock()
        mock.return_value = mock_file
        yield mock_file


@pytest.fixture(scope="function")
def sample_analysis_results() -> Dict[str, Any]:
    """Sample analysis results for testing."""
    return {
        "accuracy": 0.85,
        "feature_importance": {
            "bees_num": 0.3,
            "season_summer": 0.2,
            "site_site1": 0.15
        },
        "classification_report": {
            "precision": 0.85,
            "recall": 0.80,
            "f1-score": 0.82
        },
        "model_type": "RandomForestClassifier",
        "parameters": {"n_estimators": 100}
    }


@pytest.fixture(scope="function")
def sample_plant_recommendations() -> Dict[str, Any]:
    """Sample plant recommendations for testing."""
    return {
        "recommendations": [
            {
                "plant_species": "Sunflower",
                "score": 0.85,
                "bee_count": 5,
                "avg_bees": 5.0,
                "native_bee_ratio": 1.0,
                "rank": 1
            },
            {
                "plant_species": "Lavender",
                "score": 0.78,
                "bee_count": 7,
                "avg_bees": 7.0,
                "native_bee_ratio": 1.0,
                "rank": 2
            }
        ],
        "total_plants_analyzed": 5,
        "analysis_criteria": {
            "bee_count_weight": 0.4,
            "avg_bees_weight": 0.3,
            "native_bee_ratio_weight": 0.3
        }
    }


# Performance testing fixtures
@pytest.fixture(scope="function")
def large_dataset(test_db_session) -> Dataset:
    """Create a large dataset for performance testing."""
    # Create a large CSV file with 1000 rows
    csv_content = "sample_id,bees_num,date,season,site,native_or_non,sampling,plant_species,time,bee_species,sex,specialized_on,parasitic,nesting,status,nonnative_bee\n"
    
    for i in range(1000):
        csv_content += f"{i+1},{i%10+1},2023-06-{15+i%30:02d},summer,site{i%5+1},native,standard,Plant{i%20+1},{10+i%12:02d}:00,Bee{i%10+1},female,generalist,0,social,native,0\n"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_file = f.name
    
    dataset = Dataset(
        name="Large Test Dataset",
        description="Large dataset for performance testing",
        file_path=temp_file
    )
    test_db_session.add(dataset)
    test_db_session.commit()
    test_db_session.refresh(dataset)
    
    yield dataset
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


# Security testing fixtures
@pytest.fixture(scope="function")
def malicious_csv_file() -> Generator[str, None, None]:
    """Create a malicious CSV file for security testing."""
    malicious_content = """sample_id,bees_num,date,season,site,native_or_non,sampling,plant_species,time,bee_species,sex,specialized_on,parasitic,nesting,status,nonnative_bee
1,5,2023-06-15,summer,site1,native,standard,"<script>alert('xss')</script>",10:00,Bombus impatiens,female,generalist,0,social,native,0
2,3,2023-06-16,summer,site1,native,standard,"'; DROP TABLE datasets; --",11:00,Apis mellifera,female,generalist,0,social,native,0"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(malicious_content)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture(scope="function")
def invalid_file() -> Generator[str, None, None]:
    """Create an invalid file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is not a CSV file")
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


# Environment fixtures
@pytest.fixture(scope="function")
def test_env_vars():
    """Set test environment variables."""
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ.update({
        "DATABASE_URL": TEST_DATABASE_URL,
        "CELERY_BROKER_URL": "memory://",
        "CELERY_RESULT_BACKEND": "memory://",
        "API_SECRET_KEY": "test-secret-key-for-testing-only",
        "DEBUG": "True",
        "ENVIRONMENT": "test"
    })
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Logging fixtures
@pytest.fixture(scope="function")
def capture_logs():
    """Capture logs for testing."""
    import logging
    from io import StringIO
    
    # Create string buffer for logs
    log_buffer = StringIO()
    
    # Create handler
    handler = logging.StreamHandler(log_buffer)
    handler.setLevel(logging.DEBUG)
    
    # Get logger and add handler
    logger = logging.getLogger("pollinexus")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    yield log_buffer
    
    # Cleanup
    logger.removeHandler(handler)
    log_buffer.close() 