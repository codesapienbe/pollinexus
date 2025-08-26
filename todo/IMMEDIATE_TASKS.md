# 🎯 Immediate Tasks - Pollinexus Implementation

## 📋 Sprint 1: Foundation Setup (Week 1)

### Day 1-2: Project Structure & Dependencies

#### Task 1.1: Update Project Dependencies

**Priority**: P0 | **Estimated Time**: 2 hours

- [ ] **Update pyproject.toml with new dependencies**

  ```toml
  [project]
  dependencies = [
      # Existing dependencies...
      "fastapi>=0.104.0",
      "uvicorn[standard]>=0.24.0",
      "celery>=5.3.0",
      "redis>=5.0.0",
      "sqlalchemy>=2.0.0",
      "duckdb>=0.9.0",
      "duckdb-engine>=0.9.0",
      "pydantic>=2.5.0",
      "python-multipart>=0.0.6",
      "python-jose[cryptography]>=3.3.0",
      "passlib[bcrypt]>=1.7.4",
  ]
  ```

- [ ] **Install new dependencies**

  ```bash
  pip install -e ".[dev]"
  ```

#### Task 1.2: Create Core Package Structure

**Priority**: P0 | **Estimated Time**: 1 hour

- [ ] **Create directory structure**

  ```bash
  mkdir -p src/pollinexus/{api,core,models,services,tasks,utils}
  mkdir -p src/pollinexus/api/{routes,models}
  mkdir -p src/pollinexus/tasks
  ```

- [ ] **Create **init**.py files**

  ```bash
  touch src/pollinexus/__init__.py
  touch src/pollinexus/api/__init__.py
  touch src/pollinexus/core/__init__.py
  touch src/pollinexus/models/__init__.py
  touch src/pollinexus/services/__init__.py
  touch src/pollinexus/tasks/__init__.py
  touch src/pollinexus/utils/__init__.py
  ```

#### Task 1.3: Setup Environment Configuration

**Priority**: P0 | **Estimated Time**: 1 hour

- [ ] **Create .env file**

  ```bash
  # .env
  DATABASE_URL=duckdb:///pollinexus.db
  CELERY_BROKER_URL=memory://
  CELERY_RESULT_BACKEND=memory://
  API_SECRET_KEY=your-secret-key-here
  DEBUG=True
  ```

- [ ] **Create config.py**

  ```python
  # src/pollinexus/core/config.py
  from pydantic_settings import BaseSettings
  
  class Settings(BaseSettings):
      database_url: str
      celery_broker_url: str
      celery_result_backend: str
      api_secret_key: str
      debug: bool = False
      
      class Config:
          env_file = ".env"
  ```

### Day 3-4: Database Setup

#### Task 1.4: Database Models

**Priority**: P0 | **Estimated Time**: 3 hours

- [ ] **Create database models**

  ```python
  # src/pollinexus/models/database.py
  from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text
  from sqlalchemy.ext.declarative import declarative_base
  from sqlalchemy.orm import relationship
  from datetime import datetime
  
  Base = declarative_base()
  
  class Dataset(Base):
      __tablename__ = "datasets"
      id = Column(Integer, primary_key=True, index=True)
      name = Column(String(255), nullable=False)
      description = Column(Text)
      file_path = Column(String(500), nullable=False)
      created_at = Column(DateTime, default=datetime.utcnow)
      updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
      
      analysis_jobs = relationship("AnalysisJob", back_populates="dataset")
  
  class AnalysisJob(Base):
      __tablename__ = "analysis_jobs"
      id = Column(Integer, primary_key=True, index=True)
      dataset_id = Column(Integer, ForeignKey("datasets.id"))
      job_type = Column(String(100), nullable=False)
      status = Column(String(50), default="pending")
      parameters = Column(JSON)
      results = Column(JSON)
      created_at = Column(DateTime, default=datetime.utcnow)
      completed_at = Column(DateTime)
      celery_task_id = Column(String(255))
      
      dataset = relationship("Dataset", back_populates="analysis_jobs")
      recommendations = relationship("PlantRecommendation", back_populates="job")
  
  class PlantRecommendation(Base):
      __tablename__ = "plant_recommendations"
      id = Column(Integer, primary_key=True, index=True)
      job_id = Column(Integer, ForeignKey("analysis_jobs.id"))
      plant_species = Column(String(255), nullable=False)
      score = Column(String(10))
      rank = Column(Integer)
      reasoning = Column(Text)
      created_at = Column(DateTime, default=datetime.utcnow)
      
      job = relationship("AnalysisJob", back_populates="recommendations")
  ```

#### Task 1.5: Database Connection

**Priority**: P0 | **Estimated Time**: 2 hours

- [ ] **Create database connection**

  ```python
  # src/pollinexus/core/database.py
  from sqlalchemy import create_engine
  from sqlalchemy.orm import sessionmaker
  from sqlalchemy.ext.declarative import declarative_base
  from .config import settings
  
  engine = create_engine(settings.database_url)
  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  Base = declarative_base()
  
  def get_db():
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()
  ```

- [ ] **Create database tables**

  ```bash
  python -m pollinexus.cli init_db
  ```

### Day 5-7: FastAPI Setup

#### Task 1.6: FastAPI Application

**Priority**: P0 | **Estimated Time**: 4 hours

- [ ] **Create main FastAPI app**

  ```python
  # src/pollinexus/api/main.py
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  from .routes import datasets, analysis, visualizations
  
  app = FastAPI(
      title="Pollinexus API",
      description="Data-Driven Pollinator Conservation API",
      version="0.1.0"
  )
  
  # CORS middleware
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  
  # Include routers
  app.include_router(datasets.router, prefix="/api/v1", tags=["datasets"])
  app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])
  app.include_router(visualizations.router, prefix="/api/v1", tags=["visualizations"])
  
  @app.get("/")
  async def root():
      return {"message": "Welcome to Pollinexus API"}
  
  @app.get("/health")
  async def health_check():
      return {"status": "healthy"}
  ```

#### Task 1.7: Pydantic Models

**Priority**: P0 | **Estimated Time**: 2 hours

- [ ] **Create request/response models**

  ```python
  # src/pollinexus/api/models/requests.py
  from pydantic import BaseModel
  from typing import Optional, Dict, Any
  
  class DatasetCreate(BaseModel):
      name: str
      description: Optional[str] = None
      file_path: str
  
  class AnalysisJobCreate(BaseModel):
      dataset_id: int
      job_type: str
      parameters: Optional[Dict[str, Any]] = None
  
  class VisualizationRequest(BaseModel):
      dataset_id: int
      plot_types: list[str]
      parameters: Optional[Dict[str, Any]] = None
  ```

  ```python
  # src/pollinexus/api/models/responses.py
  from pydantic import BaseModel
  from typing import Optional, Dict, Any, List
  from datetime import datetime
  
  class DatasetResponse(BaseModel):
      id: int
      name: str
      description: Optional[str]
      file_path: str
      created_at: datetime
      updated_at: datetime
      
      class Config:
          from_attributes = True
  
  class AnalysisJobResponse(BaseModel):
      id: int
      dataset_id: int
      job_type: str
      status: str
      parameters: Optional[Dict[str, Any]]
      results: Optional[Dict[str, Any]]
      created_at: datetime
      completed_at: Optional[datetime]
      celery_task_id: Optional[str]
      
      class Config:
          from_attributes = True
  ```

## 📋 Sprint 2: Core Services (Week 2)

### Day 8-10: Data Processing Services

#### Task 2.1: Data Service Implementation

**Priority**: P1 | **Estimated Time**: 6 hours

- [ ] **Create data service**

  ```python
  # src/pollinexus/services/data_service.py
  import pandas as pd
  from typing import Dict, Any, Optional
  from pathlib import Path
  
  class DataService:
      def __init__(self):
          self.supported_formats = ['.csv', '.xlsx', '.xls']
      
      def load_dataset(self, file_path: str) -> pd.DataFrame:
          """Load dataset from file"""
          path = Path(file_path)
          if not path.exists():
              raise FileNotFoundError(f"File not found: {file_path}")
          
          if path.suffix.lower() == '.csv':
              return pd.read_csv(file_path)
          elif path.suffix.lower() in ['.xlsx', '.xls']:
              return pd.read_excel(file_path)
          else:
              raise ValueError(f"Unsupported file format: {path.suffix}")
      
      def validate_dataset(self, data: pd.DataFrame) -> Dict[str, Any]:
          """Validate dataset structure and content"""
          validation_result = {
              'is_valid': True,
              'errors': [],
              'warnings': [],
              'info': {}
          }
          
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
          
          # Check data types
          if 'bees_num' in data.columns and not pd.api.types.is_numeric_dtype(data['bees_num']):
              validation_result['warnings'].append("bees_num should be numeric")
          
          # Check for missing values
          missing_counts = data.isnull().sum()
          if missing_counts.sum() > 0:
              validation_result['info']['missing_values'] = missing_counts.to_dict()
          
          return validation_result
      
      def clean_dataset(self, data: pd.DataFrame) -> pd.DataFrame:
          """Clean and preprocess dataset"""
          cleaned_data = data.copy()
          
          # Convert data types
          if 'bees_num' in cleaned_data.columns:
              cleaned_data['bees_num'] = pd.to_numeric(cleaned_data['bees_num'], errors='coerce')
          
          if 'date' in cleaned_data.columns:
              cleaned_data['date'] = pd.to_datetime(cleaned_data['date'], errors='coerce')
          
          # Handle missing values
          cleaned_data['plant_species'] = cleaned_data['plant_species'].fillna('None')
          cleaned_data['specialized_on'] = cleaned_data['specialized_on'].fillna('Unknown')
          
          # Remove duplicates
          cleaned_data = cleaned_data.drop_duplicates()
          
          return cleaned_data
      
      def get_dataset_info(self, data: pd.DataFrame) -> Dict[str, Any]:
          """Get dataset statistics and information"""
          info = {
              'total_records': len(data),
              'total_columns': len(data.columns),
              'missing_values': data.isnull().sum().to_dict(),
              'unique_values': {},
              'data_types': data.dtypes.to_dict()
          }
          
          # Count unique values for categorical columns
          categorical_columns = ['bee_species', 'plant_species', 'site', 'season']
          for col in categorical_columns:
              if col in data.columns:
                  info['unique_values'][col] = data[col].nunique()
          
          return info
  ```

#### Task 2.2: Database Service

**Priority**: P1 | **Estimated Time**: 4 hours

- [ ] **Create database service**

  ```python
  # src/pollinexus/services/database_service.py
  from sqlalchemy.orm import Session
  from typing import List, Optional
  from ..models.database import Dataset, AnalysisJob, PlantRecommendation
  from ..api.models.requests import DatasetCreate, AnalysisJobCreate
  from ..api.models.responses import DatasetResponse, AnalysisJobResponse
  
  class DatabaseService:
      def __init__(self, db: Session):
          self.db = db
      
      def create_dataset(self, dataset: DatasetCreate) -> Dataset:
          """Create a new dataset record"""
          db_dataset = Dataset(
              name=dataset.name,
              description=dataset.description,
              file_path=dataset.file_path
          )
          self.db.add(db_dataset)
          self.db.commit()
          self.db.refresh(db_dataset)
          return db_dataset
      
      def get_dataset(self, dataset_id: int) -> Optional[Dataset]:
          """Get dataset by ID"""
          return self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
      
      def list_datasets(self) -> List[Dataset]:
          """List all datasets"""
          return self.db.query(Dataset).all()
      
      def delete_dataset(self, dataset_id: int) -> bool:
          """Delete dataset by ID"""
          dataset = self.get_dataset(dataset_id)
          if dataset:
              self.db.delete(dataset)
              self.db.commit()
              return True
          return False
      
      def create_analysis_job(self, job: AnalysisJobCreate) -> AnalysisJob:
          """Create a new analysis job"""
          db_job = AnalysisJob(
              dataset_id=job.dataset_id,
              job_type=job.job_type,
              parameters=job.parameters
          )
          self.db.add(db_job)
          self.db.commit()
          self.db.refresh(db_job)
          return db_job
      
      def get_analysis_job(self, job_id: int) -> Optional[AnalysisJob]:
          """Get analysis job by ID"""
          return self.db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
      
      def update_job_status(self, job_id: int, status: str, results: Optional[dict] = None) -> bool:
          """Update job status and results"""
          job = self.get_analysis_job(job_id)
          if job:
              job.status = status
              if results:
                  job.results = results
              if status in ['completed', 'failed']:
                  job.completed_at = datetime.utcnow()
              self.db.commit()
              return True
          return False
  ```

### Day 11-14: Celery Tasks Setup

#### Task 2.3: Celery Configuration

**Priority**: P1 | **Estimated Time**: 3 hours

- [ ] **Create Celery app**

  ```python
  # src/pollinexus/tasks/celery_app.py
  from celery import Celery
  from ..core.config import settings
  
  celery_app = Celery(
      "pollinexus",
      broker=settings.celery_broker_url,
      backend=settings.celery_result_backend,
      include=['pollinexus.tasks.analysis', 'pollinexus.tasks.visualization']
  )
  
  celery_app.conf.update(
      task_serializer='json',
      accept_content=['json'],
      result_serializer='json',
      timezone='UTC',
      enable_utc=True,
      task_track_started=True,
      task_time_limit=30 * 60,  # 30 minutes
      task_soft_time_limit=25 * 60,  # 25 minutes
  )
  ```

#### Task 2.4: Analysis Tasks

**Priority**: P1 | **Estimated Time**: 6 hours

- [ ] **Create analysis tasks**

  ```python
  # src/pollinexus/tasks/analysis.py
  from celery import current_task
  from typing import Dict, Any, List
  import pandas as pd
  from sklearn.ensemble import RandomForestClassifier
  from sklearn.model_selection import train_test_split
  from sklearn.metrics import accuracy_score, classification_report
  from ..services.data_service import DataService
  from ..services.database_service import DatabaseService
  from ..core.database import SessionLocal
  
  data_service = DataService()
  
  @celery_app.task(bind=True)
  def analyze_bee_preferences(self, dataset_id: int, parameters: Dict[str, Any] = None):
      """Analyze bee species preferences using machine learning"""
      try:
          # Update task status
          current_task.update_state(state='PROGRESS', meta={'status': 'Loading dataset'})
          
          # Get dataset
          db = SessionLocal()
          db_service = DatabaseService(db)
          dataset = db_service.get_dataset(dataset_id)
          
          if not dataset:
              raise ValueError(f"Dataset {dataset_id} not found")
          
          # Load and clean data
          data = data_service.load_dataset(dataset.file_path)
          cleaned_data = data_service.clean_dataset(data)
          
          current_task.update_state(state='PROGRESS', meta={'status': 'Preparing features'})
          
          # Prepare features for ML
          # This is a simplified example - you'll need to implement proper feature engineering
          features = cleaned_data[['bees_num', 'season', 'site', 'native_or_non']].copy()
          target = cleaned_data['nonnative_bee']
          
          # Encode categorical variables
          features_encoded = pd.get_dummies(features, columns=['season', 'site', 'native_or_non'])
          
          # Split data
          X_train, X_test, y_train, y_test = train_test_split(
              features_encoded, target, test_size=0.2, random_state=42
          )
          
          current_task.update_state(state='PROGRESS', meta={'status': 'Training model'})
          
          # Train model
          model = RandomForestClassifier(n_estimators=100, random_state=42)
          model.fit(X_train, y_train)
          
          # Make predictions
          y_pred = model.predict(X_test)
          accuracy = accuracy_score(y_test, y_pred)
          
          current_task.update_state(state='PROGRESS', meta={'status': 'Generating results'})
          
          # Prepare results
          results = {
              'accuracy': float(accuracy),
              'feature_importance': dict(zip(features_encoded.columns, model.feature_importances_)),
              'classification_report': classification_report(y_test, y_pred, output_dict=True),
              'model_type': 'RandomForestClassifier',
              'parameters': parameters or {}
          }
          
          # Update job status
          db_service.update_job_status(self.request.id, 'completed', results)
          
          return results
          
      except Exception as e:
          # Update job status to failed
          db_service.update_job_status(self.request.id, 'failed', {'error': str(e)})
          raise
      finally:
          db.close()
  
  @celery_app.task(bind=True)
  def generate_plant_recommendations(self, dataset_id: int, top_n: int = 3):
      """Generate plant species recommendations"""
      try:
          current_task.update_state(state='PROGRESS', meta={'status': 'Analyzing plant preferences'})
          
          # Get dataset
          db = SessionLocal()
          db_service = DatabaseService(db)
          dataset = db_service.get_dataset(dataset_id)
          
          if not dataset:
              raise ValueError(f"Dataset {dataset_id} not found")
          
          # Load and clean data
          data = data_service.load_dataset(dataset.file_path)
          cleaned_data = data_service.clean_dataset(data)
          
          # Analyze plant preferences
          plant_analysis = cleaned_data.groupby('plant_species').agg({
              'bees_num': ['count', 'sum', 'mean'],
              'nonnative_bee': 'mean'
          }).round(3)
          
          # Calculate preference scores
          plant_scores = []
          for plant in plant_analysis.index:
              if plant != 'None':
                  score = (
                      plant_analysis.loc[plant, ('bees_num', 'count')] * 0.4 +
                      plant_analysis.loc[plant, ('bees_num', 'mean')] * 0.3 +
                      (1 - plant_analysis.loc[plant, ('nonnative_bee', 'mean')]) * 0.3
                  )
                  plant_scores.append({
                      'plant_species': plant,
                      'score': float(score),
                      'bee_count': int(plant_analysis.loc[plant, ('bees_num', 'count')]),
                      'avg_bees': float(plant_analysis.loc[plant, ('bees_num', 'mean')]),
                      'native_bee_ratio': float(1 - plant_analysis.loc[plant, ('nonnative_bee', 'mean')])
                  })
          
          # Sort by score and get top recommendations
          plant_scores.sort(key=lambda x: x['score'], reverse=True)
          top_recommendations = plant_scores[:top_n]
          
          results = {
              'recommendations': top_recommendations,
              'total_plants_analyzed': len(plant_scores),
              'analysis_criteria': {
                  'bee_count_weight': 0.4,
                  'avg_bees_weight': 0.3,
                  'native_bee_ratio_weight': 0.3
              }
          }
          
          # Update job status
          db_service.update_job_status(self.request.id, 'completed', results)
          
          return results
          
      except Exception as e:
          db_service.update_job_status(self.request.id, 'failed', {'error': str(e)})
          raise
      finally:
          db.close()
  ```

## 📋 Sprint 3: API Endpoints (Week 3)

### Day 15-17: Dataset Management API

#### Task 3.1: Dataset Routes

**Priority**: P1 | **Estimated Time**: 4 hours

- [ ] **Create dataset routes**

  ```python
  # src/pollinexus/api/routes/datasets.py
  from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
  from sqlalchemy.orm import Session
  from typing import List
  import shutil
  import os
  from pathlib import Path
  
  from ...core.database import get_db
  from ...services.database_service import DatabaseService
  from ...services.data_service import DataService
  from ..models.requests import DatasetCreate
  from ..models.responses import DatasetResponse
  
  router = APIRouter()
  
  @router.post("/datasets/", response_model=DatasetResponse)
  async def create_dataset(
      name: str,
      description: str = None,
      file: UploadFile = File(...),
      db: Session = Depends(get_db)
  ):
      """Upload and create a new dataset"""
      # Validate file type
      if not file.filename.endswith('.csv'):
          raise HTTPException(status_code=400, detail="Only CSV files are supported")
      
      # Create upload directory
      upload_dir = Path("uploads")
      upload_dir.mkdir(exist_ok=True)
      
      # Save file
      file_path = upload_dir / file.filename
      with open(file_path, "wb") as buffer:
          shutil.copyfileobj(file.file, buffer)
      
      # Validate dataset
      data_service = DataService()
      try:
          data = data_service.load_dataset(str(file_path))
          validation = data_service.validate_dataset(data)
          
          if not validation['is_valid']:
              os.remove(file_path)
              raise HTTPException(
                  status_code=400, 
                  detail=f"Dataset validation failed: {validation['errors']}"
              )
      except Exception as e:
          os.remove(file_path)
          raise HTTPException(status_code=400, detail=f"Error loading dataset: {str(e)}")
      
      # Create dataset record
      db_service = DatabaseService(db)
      dataset_create = DatasetCreate(
          name=name,
          description=description,
          file_path=str(file_path)
      )
      dataset = db_service.create_dataset(dataset_create)
      
      return dataset
  
  @router.get("/datasets/", response_model=List[DatasetResponse])
  async def list_datasets(db: Session = Depends(get_db)):
      """List all datasets"""
      db_service = DatabaseService(db)
      return db_service.list_datasets()
  
  @router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
  async def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
      """Get dataset by ID"""
      db_service = DatabaseService(db)
      dataset = db_service.get_dataset(dataset_id)
      
      if not dataset:
          raise HTTPException(status_code=404, detail="Dataset not found")
      
      return dataset
  
  @router.delete("/datasets/{dataset_id}")
  async def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
      """Delete dataset by ID"""
      db_service = DatabaseService(db)
      dataset = db_service.get_dataset(dataset_id)
      
      if not dataset:
          raise HTTPException(status_code=404, detail="Dataset not found")
      
      # Remove file
      if os.path.exists(dataset.file_path):
          os.remove(dataset.file_path)
      
      # Remove from database
      success = db_service.delete_dataset(dataset_id)
      
      if success:
          return {"message": "Dataset deleted successfully"}
      else:
          raise HTTPException(status_code=500, detail="Failed to delete dataset")
  
  @router.get("/datasets/{dataset_id}/info")
  async def get_dataset_info(dataset_id: int, db: Session = Depends(get_db)):
      """Get dataset information and statistics"""
      db_service = DatabaseService(db)
      dataset = db_service.get_dataset(dataset_id)
      
      if not dataset:
          raise HTTPException(status_code=404, detail="Dataset not found")
      
      data_service = DataService()
      data = data_service.load_dataset(dataset.file_path)
      info = data_service.get_dataset_info(data)
      
      return {
          "dataset": dataset,
          "statistics": info
      }
  ```

### Day 18-21: Analysis API

#### Task 3.2: Analysis Routes

**Priority**: P1 | **Estimated Time**: 4 hours

- [ ] **Create analysis routes**

  ```python
  # src/pollinexus/api/routes/analysis.py
  from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
  from sqlalchemy.orm import Session
  from typing import List
  
  from ...core.database import get_db
  from ...services.database_service import DatabaseService
  from ...tasks.analysis import analyze_bee_preferences, generate_plant_recommendations
  from ..models.requests import AnalysisJobCreate
  from ..models.responses import AnalysisJobResponse
  
  router = APIRouter()
  
  @router.post("/analysis/bee-preferences/", response_model=AnalysisJobResponse)
  async def start_bee_preference_analysis(
      job: AnalysisJobCreate,
      background_tasks: BackgroundTasks,
      db: Session = Depends(get_db)
  ):
      """Start bee preference analysis"""
      db_service = DatabaseService(db)
      
      # Verify dataset exists
      dataset = db_service.get_dataset(job.dataset_id)
      if not dataset:
          raise HTTPException(status_code=404, detail="Dataset not found")
      
      # Create analysis job
      analysis_job = db_service.create_analysis_job(job)
      
      # Start Celery task
      task = analyze_bee_preferences.delay(job.dataset_id, job.parameters)
      
      # Update job with task ID
      db_service.update_job_status(analysis_job.id, 'running', {'celery_task_id': task.id})
      
      return analysis_job
  
  @router.post("/analysis/plant-recommendations/", response_model=AnalysisJobResponse)
  async def start_plant_recommendation_analysis(
      dataset_id: int,
      top_n: int = 3,
      background_tasks: BackgroundTasks,
      db: Session = Depends(get_db)
  ):
      """Start plant recommendation analysis"""
      db_service = DatabaseService(db)
      
      # Verify dataset exists
      dataset = db_service.get_dataset(dataset_id)
      if not dataset:
          raise HTTPException(status_code=404, detail="Dataset not found")
      
      # Create analysis job
      job_create = AnalysisJobCreate(
          dataset_id=dataset_id,
          job_type="plant_recommendations",
          parameters={"top_n": top_n}
      )
      analysis_job = db_service.create_analysis_job(job_create)
      
      # Start Celery task
      task = generate_plant_recommendations.delay(dataset_id, top_n)
      
      # Update job with task ID
      db_service.update_job_status(analysis_job.id, 'running', {'celery_task_id': task.id})
      
      return analysis_job
  
  @router.get("/analysis/jobs/{job_id}", response_model=AnalysisJobResponse)
  async def get_analysis_job(job_id: int, db: Session = Depends(get_db)):
      """Get analysis job by ID"""
      db_service = DatabaseService(db)
      job = db_service.get_analysis_job(job_id)
      
      if not job:
          raise HTTPException(status_code=404, detail="Analysis job not found")
      
      return job
  
  @router.get("/analysis/jobs/", response_model=List[AnalysisJobResponse])
  async def list_analysis_jobs(db: Session = Depends(get_db)):
      """List all analysis jobs"""
      db_service = DatabaseService(db)
      return db_service.list_analysis_jobs()
  
  @router.get("/analysis/jobs/{job_id}/results")
  async def get_analysis_results(job_id: int, db: Session = Depends(get_db)):
      """Get analysis results"""
      db_service = DatabaseService(db)
      job = db_service.get_analysis_job(job_id)
      
      if not job:
          raise HTTPException(status_code=404, detail="Analysis job not found")
      
      if job.status != 'completed':
          raise HTTPException(status_code=400, detail="Analysis job not completed")
      
      return {
          "job_id": job.id,
          "status": job.status,
          "results": job.results,
          "completed_at": job.completed_at
      }
  ```

## 🚀 Quick Start Commands

### Development Setup

```bash
# 1. Install dependencies
pip install -e ".[dev]"

# 2. Set up environment
cp env.example .env
# Edit .env with your database credentials

# 3. Initialize database
python -m pollinexus.cli init_db

# 4. Start FastAPI server
uvicorn pollinexus.api.main:app --reload

# 5. Start Celery worker (in new terminal)
celery -A pollinexus.tasks.celery_app worker --loglevel=info
```

### Testing the API

```bash
# 1. Load CSV directly into DuckDB
python -m pollinexus.cli load-csv todo/plants_and_bees.csv --table-name plants_and_bees

# 2. Analyze dataset
python -m pollinexus.cli analyze-dataset plants_and_bees

# 3. Get plant recommendations
python -m pollinexus.cli get-recommendations plants_and_bees --top-n 5

# 4. Upload dataset via API
curl -X POST "http://localhost:8000/api/v1/datasets/" \
  -H "Content-Type: multipart/form-data" \
  -F "name=Plants and Bees Dataset" \
  -F "description=Sample pollinator data" \
  -F "file=@todo/plants_and_bees.csv"

# 5. Start analysis
curl -X POST "http://localhost:8000/api/v1/analysis/bee-preferences/" \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": 1, "job_type": "bee_preferences"}'

# 6. Check job status
curl "http://localhost:8000/api/v1/analysis/jobs/1"

# 7. Get results
curl "http://localhost:8000/api/v1/analysis/jobs/1/results"
```

## 📊 Progress Tracking

### Week 1 Checklist

- [ ] Project structure created
- [ ] Dependencies updated
- [ ] Database models implemented
- [ ] FastAPI app configured
- [ ] Basic API endpoints working

### Week 2 Checklist

- [ ] Data service implemented
- [ ] Database service implemented
- [ ] Celery tasks configured
- [ ] Analysis tasks working
- [ ] Basic error handling

### Week 3 Checklist

- [ ] Dataset management API complete
- [ ] Analysis API complete
- [ ] File upload working
- [ ] Background task processing
- [ ] API documentation generated

## 🎯 Next Steps After Sprint 3

1. **Add visualization endpoints**
2. **Implement report generation**
3. **Add authentication and authorization**
4. **Implement caching layer**
5. **Add comprehensive testing**
6. **Performance optimization**
7. **Production deployment setup**

---

**Note**: This task breakdown focuses on the core functionality needed to get a working API with Celery tasks. Each task includes specific code examples and can be implemented incrementally.
