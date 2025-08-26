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

### Day 8-9: Logging & Monitoring Infrastructure

#### Task 2.0: Structured Logging Setup

**Priority**: P0 | **Estimated Time**: 4 hours

- [ ] **Create structured logging configuration**

  ```python
  # src/pollinexus/core/logging.py
  import logging
  import json
  import sys
  from datetime import datetime
  from typing import Any, Dict, Optional
  from contextvars import ContextVar
  import uuid
  
  # Context variables for request tracking
  request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
  user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
  correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
  
  class StructuredFormatter(logging.Formatter):
      """JSON structured formatter for OpenTelemetry compatibility."""
      
      def format(self, record: logging.LogRecord) -> str:
          log_entry = {
              'timestamp': datetime.utcnow().isoformat() + 'Z',
              'level': record.levelname,
              'logger': record.name,
              'message': record.getMessage(),
              'module': record.module,
              'function': record.funcName,
              'line': record.lineno,
              'request_id': request_id.get(),
              'user_id': user_id.get(),
              'correlation_id': correlation_id.get(),
              'thread_id': record.thread,
              'process_id': record.process
          }
          
          # Add exception info if present
          if record.exc_info:
              log_entry['exception'] = self.formatException(record.exc_info)
          
          # Add extra fields
          if hasattr(record, 'extra_fields'):
              log_entry.update(record.extra_fields)
          
          return json.dumps(log_entry)
  
  class StructuredLogger:
      """Structured logger with OpenTelemetry-friendly output."""
      
      def __init__(self, name: str):
          self.logger = logging.getLogger(name)
          self.logger.setLevel(logging.INFO)
          
          # Add JSON formatter
          handler = logging.StreamHandler(sys.stdout)
          handler.setFormatter(StructuredFormatter())
          self.logger.addHandler(handler)
      
      def _log(self, level: int, message: str, **kwargs):
          """Internal logging method with extra fields."""
          extra_fields = {
              'component': self.logger.name,
              'timestamp': datetime.utcnow().isoformat() + 'Z'
          }
          extra_fields.update(kwargs)
          
          record = self.logger.makeRecord(
              self.logger.name, level, '', 0, message, (), None
          )
          record.extra_fields = extra_fields
          self.logger.handle(record)
      
      def debug(self, message: str, **kwargs):
          self._log(logging.DEBUG, message, **kwargs)
      
      def info(self, message: str, **kwargs):
          self._log(logging.INFO, message, **kwargs)
      
      def warning(self, message: str, **kwargs):
          self._log(logging.WARNING, message, **kwargs)
      
      def error(self, message: str, **kwargs):
          self._log(logging.ERROR, message, **kwargs)
      
      def critical(self, message: str, **kwargs):
          self._log(logging.CRITICAL, message, **kwargs)
  
  # Global logger instance
  logger = StructuredLogger('pollinexus')
  ```

- [ ] **Create logging middleware for FastAPI**

  ```python
  # src/pollinexus/api/middleware/logging.py
  from fastapi import Request, Response
  import time
  import uuid
  from typing import Callable
  from ...core.logging import logger, request_id, user_id, correlation_id
  
  async def logging_middleware(request: Request, call_next: Callable) -> Response:
      """Middleware for structured request/response logging."""
      
      # Generate request tracking IDs
      req_id = str(uuid.uuid4())
      corr_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
      
      # Set context variables
      request_id.set(req_id)
      correlation_id.set(corr_id)
      
      # Extract user info (if authentication is implemented)
      user = getattr(request.state, 'user', None)
      if user:
          user_id.set(str(user.id))
      
      # Log request start
      start_time = time.time()
      logger.info(
          "Request started",
          method=request.method,
          url=str(request.url),
          client_ip=request.client.host if request.client else None,
          user_agent=request.headers.get('user-agent'),
          request_id=req_id,
          correlation_id=corr_id
      )
      
      try:
          response = await call_next(request)
          
          # Log successful response
          process_time = time.time() - start_time
          logger.info(
              "Request completed",
              method=request.method,
              url=str(request.url),
              status_code=response.status_code,
              process_time=process_time,
              request_id=req_id,
              correlation_id=corr_id
          )
          
          # Add headers for tracking
          response.headers["X-Request-ID"] = req_id
          response.headers["X-Correlation-ID"] = corr_id
          response.headers["X-Process-Time"] = str(process_time)
          
          return response
          
      except Exception as e:
          # Log error response
          process_time = time.time() - start_time
          logger.error(
              "Request failed",
              method=request.method,
              url=str(request.url),
              error=str(e),
              process_time=process_time,
              request_id=req_id,
              correlation_id=corr_id
          )
          raise
      finally:
          # Clear context variables
          request_id.set(None)
          correlation_id.set(None)
          user_id.set(None)
  ```

#### Task 2.1: Service-Level Logging

**Priority**: P0 | **Estimated Time**: 3 hours

- [ ] **Update DuckDBService with comprehensive logging**

  ```python
  # src/pollinexus/services/duckdb_service.py
  # Add to existing DuckDBService class
  
  from ..core.logging import logger
  
  def load_csv_direct(self, csv_path: str, table_name: str = None) -> str:
      """Load CSV file directly into DuckDB with logging."""
      
      logger.info(
          "Starting CSV load operation",
          csv_path=csv_path,
          table_name=table_name,
          operation="csv_load"
      )
      
      try:
          if table_name is None:
              table_name = Path(csv_path).stem
          
          # Create table from CSV
          query = f"""
          CREATE TABLE IF NOT EXISTS {table_name} AS
          SELECT * FROM read_csv_auto('{csv_path}')
          """
          
          logger.debug(
              "Executing CSV load query",
              query=query,
              table_name=table_name
          )
          
          self.connection.execute(query)
          
          # Get row count
          count = self.connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
          
          logger.info(
              "CSV load completed successfully",
              csv_path=csv_path,
              table_name=table_name,
              row_count=count,
              operation="csv_load"
          )
          
          return table_name
          
      except Exception as e:
          logger.error(
              "CSV load failed",
              csv_path=csv_path,
              table_name=table_name,
              error=str(e),
              operation="csv_load"
          )
          raise
  
  def analyze_bee_preferences(self, table_name: str) -> Dict[str, Any]:
      """Analyze bee preferences with comprehensive logging."""
      
      logger.info(
          "Starting bee preference analysis",
          table_name=table_name,
          operation="bee_analysis"
      )
      
      try:
          # Log analysis steps
          logger.debug("Analyzing bee species distribution", table_name=table_name)
          bee_analysis_query = f"""
          SELECT
              bee_species,
              COUNT(*) as observation_count,
              AVG(bees_num) as avg_bees_per_observation,
              SUM(bees_num) as total_bees,
              AVG(CASE WHEN nonnative_bee = 0 THEN 1.0 ELSE 0.0 END) as native_bee_ratio
          FROM {table_name}
          WHERE bee_species IS NOT NULL
          GROUP BY bee_species
          ORDER BY total_bees DESC
          """
          
          bee_analysis = self.query_to_dataframe(bee_analysis_query)
          
          logger.debug(
              "Bee species analysis completed",
              table_name=table_name,
              species_count=len(bee_analysis)
          )
          
          # Continue with other analyses...
          logger.debug("Analyzing plant preferences", table_name=table_name)
          plant_analysis = self.query_to_dataframe(plant_analysis_query)
          
          logger.debug("Analyzing seasonal patterns", table_name=table_name)
          seasonal_analysis = self.query_to_dataframe(seasonal_analysis_query)
          
          logger.debug("Analyzing site comparisons", table_name=table_name)
          site_analysis = self.query_to_dataframe(site_analysis_query)
          
          # Prepare results
          results = {
              'bee_species_analysis': bee_analysis.to_dict('records'),
              'plant_species_analysis': plant_analysis.to_dict('records'),
              'seasonal_analysis': seasonal_analysis.to_dict('records'),
              'site_analysis': site_analysis.to_dict('records'),
              'summary': {
                  'total_observations': bee_analysis['observation_count'].sum(),
                  'total_bees': bee_analysis['total_bees'].sum(),
                  'unique_bee_species': len(bee_analysis),
                  'unique_plant_species': len(plant_analysis)
              }
          }
          
          logger.info(
              "Bee preference analysis completed successfully",
              table_name=table_name,
              total_observations=results['summary']['total_observations'],
              total_bees=results['summary']['total_bees'],
              unique_bee_species=results['summary']['unique_bee_species'],
              unique_plant_species=results['summary']['unique_plant_species'],
              operation="bee_analysis"
          )
          
          return results
          
      except Exception as e:
          logger.error(
              "Bee preference analysis failed",
              table_name=table_name,
              error=str(e),
              operation="bee_analysis"
          )
          raise
  ```

#### Task 2.2: Database Service Logging

**Priority**: P0 | **Estimated Time**: 2 hours

- [ ] **Update DatabaseService with operation logging**

  ```python
  # src/pollinexus/services/database_service.py
  # Add to existing DatabaseService class
  
  from ..core.logging import logger
  
  def create_dataset(self, dataset: DatasetCreate) -> Dataset:
      """Create a new dataset record with logging."""
      
      logger.info(
          "Creating new dataset",
          dataset_name=dataset.name,
          file_path=dataset.file_path,
          operation="dataset_create"
      )
      
      try:
          db_dataset = Dataset(
              name=dataset.name,
              description=dataset.description,
              file_path=dataset.file_path
          )
          self.db.add(db_dataset)
          self.db.commit()
          self.db.refresh(db_dataset)
          
          logger.info(
              "Dataset created successfully",
              dataset_id=db_dataset.id,
              dataset_name=dataset.name,
              operation="dataset_create"
          )
          
          return db_dataset
          
      except Exception as e:
          logger.error(
              "Dataset creation failed",
              dataset_name=dataset.name,
              error=str(e),
              operation="dataset_create"
          )
          self.db.rollback()
          raise
  
  def update_job_status(self, job_id: int, status: str, results: Optional[dict] = None) -> bool:
      """Update job status with logging."""
      
      logger.info(
          "Updating job status",
          job_id=job_id,
          new_status=status,
          operation="job_status_update"
      )
      
      try:
          job = self.get_analysis_job(job_id)
          if job:
              job.status = status
              if results:
                  job.results = results
              if status in ['completed', 'failed']:
                  job.completed_at = datetime.utcnow()
              self.db.commit()
              
              logger.info(
                  "Job status updated successfully",
                  job_id=job_id,
                  status=status,
                  operation="job_status_update"
              )
              return True
          else:
              logger.warning(
                  "Job not found for status update",
                  job_id=job_id,
                  operation="job_status_update"
              )
              return False
              
      except Exception as e:
          logger.error(
              "Job status update failed",
              job_id=job_id,
              error=str(e),
              operation="job_status_update"
          )
          self.db.rollback()
          raise
  ```

### Day 10-11: Celery Task Logging

#### Task 2.3: Celery Task Monitoring

**Priority**: P0 | **Estimated Time**: 3 hours

- [ ] **Update Celery tasks with comprehensive logging**

  ```python
  # src/pollinexus/tasks/analysis.py
  # Add to existing analysis tasks
  
  from ..core.logging import logger, correlation_id
  import uuid
  
  @celery_app.task(bind=True)
  def analyze_bee_preferences(self, dataset_id: int, parameters: Dict[str, Any] = None):
      """Analyze bee species preferences with comprehensive logging."""
      
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
      
      try:
          # Update task status
          current_task.update_state(
              state='PROGRESS',
              meta={'status': 'Loading dataset', 'correlation_id': task_correlation_id}
          )
          
          logger.debug(
              "Loading dataset for analysis",
              task_id=self.request.id,
              dataset_id=dataset_id,
              correlation_id=task_correlation_id
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
              meta={'status': 'Preparing features', 'correlation_id': task_correlation_id}
          )
          
          # Continue with ML analysis...
          logger.debug(
              "Preparing features for ML",
              task_id=self.request.id,
              dataset_id=dataset_id,
              correlation_id=task_correlation_id
          )
          
          # ... (rest of the analysis logic with logging)
          
          logger.info(
              "Bee preference analysis completed successfully",
              task_id=self.request.id,
              dataset_id=dataset_id,
              accuracy=accuracy,
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
          db_service.update_job_status(self.request.id, 'failed', {'error': str(e)})
          raise
      finally:
          db.close()
          correlation_id.set(None)
  ```

#### Task 2.4: API Route Logging

**Priority**: P0 | **Estimated Time**: 2 hours

- [ ] **Add comprehensive logging to all API routes**

  ```python
  # src/pollinexus/api/routes/datasets.py
  # Add to existing dataset routes
  
  from ...core.logging import logger
  
  @router.post("/datasets/", response_model=DatasetResponse)
  async def create_dataset(
      name: str,
      description: str = None,
      file: UploadFile = File(...),
      db: Session = Depends(get_db)
  ):
      """Upload and create a new dataset with logging."""
      
      logger.info(
          "Dataset upload request received",
          dataset_name=name,
          file_name=file.filename,
          file_size=file.size,
          operation="dataset_upload"
      )
      
      try:
          # Validate file type
          if not file.filename.endswith('.csv'):
              logger.warning(
                  "Invalid file type attempted",
                  file_name=file.filename,
                  operation="dataset_upload"
              )
              raise HTTPException(status_code=400, detail="Only CSV files are supported")
          
          # Create upload directory
          upload_dir = Path("uploads")
          upload_dir.mkdir(exist_ok=True)
          
          # Save file
          file_path = upload_dir / file.filename
          with open(file_path, "wb") as buffer:
              shutil.copyfileobj(file.file, buffer)
          
          logger.debug(
              "File saved successfully",
              file_path=str(file_path),
              operation="dataset_upload"
          )
          
          # Validate dataset
          data_service = DataService()
          try:
              data = data_service.load_dataset(str(file_path))
              validation = data_service.validate_dataset(data)
              
              logger.info(
                  "Dataset validation completed",
                  validation_result=validation['is_valid'],
                  errors=validation['errors'],
                  warnings=validation['warnings'],
                  operation="dataset_upload"
              )
              
              if not validation['is_valid']:
                  os.remove(file_path)
                  raise HTTPException(
                      status_code=400, 
                      detail=f"Dataset validation failed: {validation['errors']}"
                  )
          except Exception as e:
              os.remove(file_path)
              logger.error(
                  "Dataset validation failed",
                  error=str(e),
                  operation="dataset_upload"
              )
              raise HTTPException(status_code=400, detail=f"Error loading dataset: {str(e)}")
          
          # Create dataset record
          db_service = DatabaseService(db)
          dataset_create = DatasetCreate(
              name=name,
              description=description,
              file_path=str(file_path)
          )
          dataset = db_service.create_dataset(dataset_create)
          
          logger.info(
              "Dataset created successfully via API",
              dataset_id=dataset.id,
              dataset_name=name,
              operation="dataset_upload"
          )
          
          return dataset
          
      except HTTPException:
          raise
      except Exception as e:
          logger.error(
              "Unexpected error in dataset upload",
              error=str(e),
              operation="dataset_upload"
          )
          raise HTTPException(status_code=500, detail="Internal server error")
  ```

#### Task 2.5: CLI Command Logging

**Priority**: P1 | **Estimated Time**: 2 hours

- [ ] **Add logging to CLI commands**

  ```python
  # src/pollinexus/cli.py
  # Add to existing CLI commands
  
  from .core.logging import logger
  
  @click.command()
  @click.argument('csv_path', type=click.Path(exists=True))
  @click.option('--table-name', help='Table name for the data')
  def load_csv(csv_path, table_name):
      """Load CSV file directly into DuckDB with logging."""
      
      logger.info(
          "CLI CSV load command executed",
          csv_path=csv_path,
          table_name=table_name,
          operation="cli_csv_load"
      )
      
      try:
          with DuckDBService() as db_service:
              result_table = db_service.load_csv_direct(csv_path, table_name)
              
              logger.info(
                  "CLI CSV load completed successfully",
                  csv_path=csv_path,
                  table_name=result_table,
                  operation="cli_csv_load"
              )
              
              click.echo(f"Successfully loaded {csv_path} into table '{result_table}'")
              
      except Exception as e:
          logger.error(
              "CLI CSV load failed",
              csv_path=csv_path,
              error=str(e),
              operation="cli_csv_load"
          )
          click.echo(f"Error loading CSV: {e}", err=True)
          sys.exit(1)
  ```

#### Task 2.6: Performance Monitoring

**Priority**: P1 | **Estimated Time**: 3 hours

- [ ] **Add performance metrics logging**

  ```python
  # src/pollinexus/core/metrics.py
  import time
  from functools import wraps
  from typing import Dict, Any, Callable
  from .logging import logger
  
  class PerformanceMonitor:
      """Monitor and log performance metrics."""
      
      def __init__(self):
          self.metrics = {}
      
      def log_operation_time(self, operation: str, duration: float, **kwargs):
          """Log operation execution time."""
          logger.info(
              "Operation performance",
              operation=operation,
              duration=duration,
              **kwargs
          )
      
      def log_memory_usage(self, operation: str, memory_mb: float, **kwargs):
          """Log memory usage for operations."""
          logger.info(
              "Memory usage",
              operation=operation,
              memory_mb=memory_mb,
              **kwargs
          )
      
      def log_database_query_time(self, query: str, duration: float, **kwargs):
          """Log database query performance."""
          logger.debug(
              "Database query performance",
              query=query[:100] + "..." if len(query) > 100 else query,
              duration=duration,
              **kwargs
          )
  
  # Global performance monitor
  performance_monitor = PerformanceMonitor()
  
  def monitor_performance(operation: str):
      """Decorator to monitor function performance."""
      def decorator(func: Callable) -> Callable:
          @wraps(func)
          def wrapper(*args, **kwargs):
              start_time = time.time()
              start_memory = get_memory_usage()
              
              try:
                  result = func(*args, **kwargs)
                  
                  duration = time.time() - start_time
                  end_memory = get_memory_usage()
                  memory_used = end_memory - start_memory
                  
                  performance_monitor.log_operation_time(
                      operation=operation,
                      duration=duration,
                      memory_mb=memory_used
                  )
                  
                  return result
                  
              except Exception as e:
                  duration = time.time() - start_time
                  logger.error(
                      "Operation failed",
                      operation=operation,
                      duration=duration,
                      error=str(e)
                  )
                  raise
          
          return wrapper
      return decorator
  
  def get_memory_usage() -> float:
      """Get current memory usage in MB."""
      import psutil
      process = psutil.Process()
      return process.memory_info().rss / 1024 / 1024  # Convert to MB
  ```

#### Task 2.7: Error Tracking and Alerting

**Priority**: P1 | **Estimated Time**: 2 hours

- [ ] **Create error tracking and alerting system**

  ```python
  # src/pollinexus/core/error_tracking.py
  from typing import Dict, Any, Optional
  from .logging import logger
  import traceback
  
  class ErrorTracker:
      """Track and categorize errors for monitoring."""
      
      def __init__(self):
          self.error_counts = {}
          self.error_thresholds = {
              'database_connection': 5,
              'file_upload': 10,
              'analysis_failure': 3,
              'validation_error': 20
          }
      
      def track_error(self, error_type: str, error: Exception, context: Dict[str, Any] = None):
          """Track an error occurrence."""
          
          # Increment error count
          self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
          
          # Log error with context
          logger.error(
              "Error tracked",
              error_type=error_type,
              error_message=str(error),
              error_count=self.error_counts[error_type],
              context=context or {},
              stack_trace=traceback.format_exc()
          )
          
          # Check if threshold exceeded
          threshold = self.error_thresholds.get(error_type, 10)
          if self.error_counts[error_type] >= threshold:
              self._trigger_alert(error_type, error, context)
      
      def _trigger_alert(self, error_type: str, error: Exception, context: Dict[str, Any]):
          """Trigger alert for error threshold exceeded."""
          
          logger.critical(
              "Error threshold exceeded - alert triggered",
              error_type=error_type,
              error_count=self.error_counts[error_type],
              threshold=self.error_thresholds.get(error_type, 10),
              error_message=str(error),
              context=context or {}
          )
          
          # TODO: Integrate with external alerting system (Slack, email, etc.)
          # For now, just log the alert
      
      def get_error_summary(self) -> Dict[str, Any]:
          """Get summary of tracked errors."""
          return {
              'error_counts': self.error_counts,
              'thresholds': self.error_thresholds,
              'total_errors': sum(self.error_counts.values())
          }
  
  # Global error tracker
  error_tracker = ErrorTracker()
  
  def track_errors(error_type: str):
      """Decorator to automatically track errors."""
      def decorator(func):
          def wrapper(*args, **kwargs):
              try:
                  return func(*args, **kwargs)
              except Exception as e:
                  context = {
                      'function': func.__name__,
                      'args': str(args),
                      'kwargs': str(kwargs)
                  }
                  error_tracker.track_error(error_type, e, context)
                  raise
          return wrapper
      return decorator
  ```

#### Task 2.8: Health Check Monitoring

**Priority**: P1 | **Estimated Time**: 2 hours

- [ ] **Enhance health check endpoints with monitoring**

  ```python
  # src/pollinexus/api/health.py
  from fastapi import APIRouter, Depends
  from sqlalchemy.orm import Session
  from ..core.database import get_db
  from ..core.logging import logger
  from ..core.metrics import performance_monitor
  from ..core.error_tracking import error_tracker
  import time
  import psutil
  
  router = APIRouter()
  
  @router.get("/health")
  async def health_check():
      """Enhanced health check with system metrics."""
      
      start_time = time.time()
      
      try:
          # Basic system metrics
          cpu_percent = psutil.cpu_percent(interval=1)
          memory = psutil.virtual_memory()
          disk = psutil.disk_usage('/')
          
          # Database health check
          db_status = "healthy"
          try:
              db = next(get_db())
              db.execute("SELECT 1")
              db.close()
          except Exception as e:
              db_status = "unhealthy"
              logger.error("Database health check failed", error=str(e))
          
          # Celery health check
          celery_status = "healthy"
          try:
              # TODO: Implement Celery health check
              pass
          except Exception as e:
              celery_status = "unhealthy"
              logger.error("Celery health check failed", error=str(e))
          
          # Error summary
          error_summary = error_tracker.get_error_summary()
          
          health_data = {
              "status": "healthy" if db_status == "healthy" and celery_status == "healthy" else "degraded",
              "timestamp": time.time(),
              "version": "0.1.0",
              "services": {
                  "database": db_status,
                  "celery": celery_status
              },
              "system": {
                  "cpu_percent": cpu_percent,
                  "memory_percent": memory.percent,
                  "disk_percent": disk.percent
              },
              "errors": error_summary,
              "response_time": time.time() - start_time
          }
          
          logger.info(
              "Health check completed",
              status=health_data["status"],
              response_time=health_data["response_time"],
              cpu_percent=cpu_percent,
              memory_percent=memory.percent
          )
          
          return health_data
          
      except Exception as e:
          logger.error("Health check failed", error=str(e))
          return {
              "status": "unhealthy",
              "timestamp": time.time(),
              "error": str(e)
          }
  
  @router.get("/metrics")
  async def get_metrics():
      """Get system metrics for monitoring."""
      
      try:
          # System metrics
          cpu_percent = psutil.cpu_percent(interval=1)
          memory = psutil.virtual_memory()
          disk = psutil.disk_usage('/')
          
          # Process metrics
          process = psutil.Process()
          process_memory = process.memory_info().rss / 1024 / 1024  # MB
          
          metrics = {
              "timestamp": time.time(),
              "system": {
                  "cpu_percent": cpu_percent,
                  "memory_percent": memory.percent,
                  "memory_available_mb": memory.available / 1024 / 1024,
                  "disk_percent": disk.percent,
                  "disk_free_mb": disk.free / 1024 / 1024
              },
              "process": {
                  "memory_mb": process_memory,
                  "cpu_percent": process.cpu_percent(),
                  "threads": process.num_threads(),
                  "open_files": len(process.open_files()),
                  "connections": len(process.connections())
              },
              "errors": error_tracker.get_error_summary()
          }
          
          logger.debug("Metrics collected", metrics=metrics)
          
          return metrics
          
      except Exception as e:
          logger.error("Metrics collection failed", error=str(e))
          raise
  ```

### Day 12-14: Data Processing Services

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
