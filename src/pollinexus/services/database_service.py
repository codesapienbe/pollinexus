"""
Database service for Pollinexus.

This service handles all database operations with comprehensive logging
and monitoring for the Pollinexus application.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import time

from ..models.database import Dataset, AnalysisJob, PlantRecommendation, AnalysisResult
from ..api.models.requests import DatasetCreate, AnalysisJobCreate, DatasetUpdate, AnalysisJobUpdate
from ..api.models.responses import DatasetResponse, AnalysisJobResponse
from ..core.logging import logger
from ..core.metrics import monitor_performance
from ..core.error_tracking import track_errors, error_tracker


class DatabaseService:
    """Service for database operations with comprehensive logging."""
    
    def __init__(self, db: Session):
        self.db = db
        logger.debug("DatabaseService initialized", session_id=id(db))
    
    @monitor_performance("dataset_create")
    @track_errors("database_operation")
    def create_dataset(self, dataset: DatasetCreate) -> Dataset:
        """Create a new dataset record with comprehensive logging."""
        
        logger.info(
            "Creating new dataset",
            dataset_name=dataset.name,
            file_path=dataset.file_path,
            operation="dataset_create"
        )
        
        start_time = time.time()
        
        try:
            db_dataset = Dataset(
                name=dataset.name,
                description=dataset.description,
                file_path=dataset.file_path
            )
            
            self.db.add(db_dataset)
            self.db.commit()
            self.db.refresh(db_dataset)
            
            operation_time = time.time() - start_time
            
            logger.info(
                "Dataset created successfully",
                dataset_id=db_dataset.id,
                dataset_name=dataset.name,
                operation_time=operation_time,
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
    
    @monitor_performance("dataset_get")
    @track_errors("database_operation")
    def get_dataset(self, dataset_id: int) -> Optional[Dataset]:
        """Get dataset by ID with logging."""
        
        logger.debug(
            "Fetching dataset by ID",
            dataset_id=dataset_id,
            operation="dataset_get"
        )
        
        try:
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if dataset:
                logger.debug(
                    "Dataset found",
                    dataset_id=dataset_id,
                    dataset_name=dataset.name,
                    operation="dataset_get"
                )
            else:
                logger.warning(
                    "Dataset not found",
                    dataset_id=dataset_id,
                    operation="dataset_get"
                )
            
            return dataset
            
        except Exception as e:
            logger.error(
                "Dataset fetch failed",
                dataset_id=dataset_id,
                error=str(e),
                operation="dataset_get"
            )
            raise
    
    @monitor_performance("dataset_list")
    @track_errors("database_operation")
    def list_datasets(self, skip: int = 0, limit: int = 100, 
                     search: Optional[str] = None) -> List[Dataset]:
        """List datasets with pagination and search."""
        
        logger.info(
            "Listing datasets",
            skip=skip,
            limit=limit,
            search=search,
            operation="dataset_list"
        )
        
        try:
            query = self.db.query(Dataset)
            
            if search:
                search_filter = or_(
                    Dataset.name.ilike(f"%{search}%"),
                    Dataset.description.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)
                logger.debug("Applied search filter", search_term=search)
            
            datasets = query.offset(skip).limit(limit).all()
            
            logger.info(
                "Datasets listed successfully",
                count=len(datasets),
                skip=skip,
                limit=limit,
                operation="dataset_list"
            )
            
            return datasets
            
        except Exception as e:
            logger.error(
                "Dataset listing failed",
                error=str(e),
                operation="dataset_list"
            )
            raise
    
    @monitor_performance("dataset_update")
    @track_errors("database_operation")
    def update_dataset(self, dataset_id: int, dataset_update: DatasetUpdate) -> Optional[Dataset]:
        """Update dataset with logging."""
        
        logger.info(
            "Updating dataset",
            dataset_id=dataset_id,
            update_fields=list(dataset_update.dict(exclude_unset=True).keys()),
            operation="dataset_update"
        )
        
        try:
            dataset = self.get_dataset(dataset_id)
            if not dataset:
                logger.warning(
                    "Dataset not found for update",
                    dataset_id=dataset_id,
                    operation="dataset_update"
                )
                return None
            
            update_data = dataset_update.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(dataset, field, value)
            
            dataset.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(dataset)
            
            logger.info(
                "Dataset updated successfully",
                dataset_id=dataset_id,
                updated_fields=list(update_data.keys()),
                operation="dataset_update"
            )
            
            return dataset
            
        except Exception as e:
            logger.error(
                "Dataset update failed",
                dataset_id=dataset_id,
                error=str(e),
                operation="dataset_update"
            )
            self.db.rollback()
            raise
    
    @monitor_performance("dataset_delete")
    @track_errors("database_operation")
    def delete_dataset(self, dataset_id: int) -> bool:
        """Delete dataset by ID with comprehensive logging."""
        
        logger.info(
            "Deleting dataset",
            dataset_id=dataset_id,
            operation="dataset_delete"
        )
        
        try:
            dataset = self.get_dataset(dataset_id)
            if not dataset:
                logger.warning(
                    "Dataset not found for deletion",
                    dataset_id=dataset_id,
                    operation="dataset_delete"
                )
                return False
            
            # Check for related analysis jobs
            related_jobs = self.db.query(AnalysisJob).filter(
                AnalysisJob.dataset_id == dataset_id
            ).count()
            
            if related_jobs > 0:
                logger.warning(
                    "Dataset has related analysis jobs",
                    dataset_id=dataset_id,
                    related_jobs_count=related_jobs,
                    operation="dataset_delete"
                )
            
            self.db.delete(dataset)
            self.db.commit()
            
            logger.info(
                "Dataset deleted successfully",
                dataset_id=dataset_id,
                related_jobs_deleted=related_jobs,
                operation="dataset_delete"
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Dataset deletion failed",
                dataset_id=dataset_id,
                error=str(e),
                operation="dataset_delete"
            )
            self.db.rollback()
            raise
    
    @monitor_performance("analysis_job_create")
    @track_errors("database_operation")
    def create_analysis_job(self, job: AnalysisJobCreate) -> AnalysisJob:
        """Create a new analysis job with logging."""
        
        logger.info(
            "Creating new analysis job",
            dataset_id=job.dataset_id,
            job_type=job.job_type,
            parameters=job.parameters,
            operation="analysis_job_create"
        )
        
        start_time = time.time()
        
        try:
            # Verify dataset exists
            dataset = self.get_dataset(job.dataset_id)
            if not dataset:
                raise ValueError(f"Dataset {job.dataset_id} not found")
            
            db_job = AnalysisJob(
                dataset_id=job.dataset_id,
                job_type=job.job_type,
                parameters=job.parameters,
                status="pending"
            )
            
            self.db.add(db_job)
            self.db.commit()
            self.db.refresh(db_job)
            
            operation_time = time.time() - start_time
            
            logger.info(
                "Analysis job created successfully",
                job_id=db_job.id,
                dataset_id=job.dataset_id,
                job_type=job.job_type,
                operation_time=operation_time,
                operation="analysis_job_create"
            )
            
            return db_job
            
        except Exception as e:
            logger.error(
                "Analysis job creation failed",
                dataset_id=job.dataset_id,
                job_type=job.job_type,
                error=str(e),
                operation="analysis_job_create"
            )
            self.db.rollback()
            raise
    
    @monitor_performance("analysis_job_get")
    @track_errors("database_operation")
    def get_analysis_job(self, job_id: int) -> Optional[AnalysisJob]:
        """Get analysis job by ID with logging."""
        
        logger.debug(
            "Fetching analysis job by ID",
            job_id=job_id,
            operation="analysis_job_get"
        )
        
        try:
            job = self.db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
            
            if job:
                logger.debug(
                    "Analysis job found",
                    job_id=job_id,
                    job_type=job.job_type,
                    status=job.status,
                    operation="analysis_job_get"
                )
            else:
                logger.warning(
                    "Analysis job not found",
                    job_id=job_id,
                    operation="analysis_job_get"
                )
            
            return job
            
        except Exception as e:
            logger.error(
                "Analysis job fetch failed",
                job_id=job_id,
                error=str(e),
                operation="analysis_job_get"
            )
            raise
    
    @monitor_performance("analysis_job_list")
    @track_errors("database_operation")
    def list_analysis_jobs(self, dataset_id: Optional[int] = None, 
                          status: Optional[str] = None,
                          skip: int = 0, limit: int = 100) -> List[AnalysisJob]:
        """List analysis jobs with filtering and pagination."""
        
        logger.info(
            "Listing analysis jobs",
            dataset_id=dataset_id,
            status=status,
            skip=skip,
            limit=limit,
            operation="analysis_job_list"
        )
        
        try:
            query = self.db.query(AnalysisJob)
            
            if dataset_id:
                query = query.filter(AnalysisJob.dataset_id == dataset_id)
                logger.debug("Applied dataset filter", dataset_id=dataset_id)
            
            if status:
                query = query.filter(AnalysisJob.status == status)
                logger.debug("Applied status filter", status=status)
            
            jobs = query.order_by(desc(AnalysisJob.created_at)).offset(skip).limit(limit).all()
            
            logger.info(
                "Analysis jobs listed successfully",
                count=len(jobs),
                dataset_id=dataset_id,
                status=status,
                operation="analysis_job_list"
            )
            
            return jobs
            
        except Exception as e:
            logger.error(
                "Analysis job listing failed",
                error=str(e),
                operation="analysis_job_list"
            )
            raise
    
    @monitor_performance("analysis_job_update")
    @track_errors("database_operation")
    def update_job_status(self, job_id: int, status: str, 
                         results: Optional[dict] = None,
                         celery_task_id: Optional[str] = None) -> bool:
        """Update job status and results with logging."""
        
        logger.info(
            "Updating job status",
            job_id=job_id,
            new_status=status,
            has_results=results is not None,
            celery_task_id=celery_task_id,
            operation="analysis_job_update"
        )
        
        try:
            job = self.get_analysis_job(job_id)
            if not job:
                logger.warning(
                    "Job not found for status update",
                    job_id=job_id,
                    operation="analysis_job_update"
                )
                return False
            
            job.status = status
            if results:
                job.results = results
            if celery_task_id:
                job.celery_task_id = celery_task_id
            
            if status in ['completed', 'failed']:
                job.completed_at = datetime.utcnow()
                logger.info(
                    "Job marked as completed/failed",
                    job_id=job_id,
                    status=status,
                    duration=job.completed_at - job.created_at if job.completed_at else None,
                    operation="analysis_job_update"
                )
            
            self.db.commit()
            
            logger.info(
                "Job status updated successfully",
                job_id=job_id,
                status=status,
                operation="analysis_job_update"
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Job status update failed",
                job_id=job_id,
                error=str(e),
                operation="analysis_job_update"
            )
            self.db.rollback()
            raise
    
    @monitor_performance("analysis_job_delete")
    @track_errors("database_operation")
    def delete_analysis_job(self, job_id: int) -> bool:
        """Delete analysis job with logging."""
        
        logger.info(
            "Deleting analysis job",
            job_id=job_id,
            operation="analysis_job_delete"
        )
        
        try:
            job = self.get_analysis_job(job_id)
            if not job:
                logger.warning(
                    "Analysis job not found for deletion",
                    job_id=job_id,
                    operation="analysis_job_delete"
                )
                return False
            
            self.db.delete(job)
            self.db.commit()
            
            logger.info(
                "Analysis job deleted successfully",
                job_id=job_id,
                operation="analysis_job_delete"
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Analysis job deletion failed",
                job_id=job_id,
                error=str(e),
                operation="analysis_job_delete"
            )
            self.db.rollback()
            raise
    
    @monitor_performance("database_stats")
    @track_errors("database_operation")
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics with logging."""
        
        logger.info("Generating database statistics", operation="database_stats")
        
        try:
            # Count datasets
            dataset_count = self.db.query(Dataset).count()
            
            # Count analysis jobs by status
            job_stats = {}
            for status in ['pending', 'running', 'completed', 'failed']:
                count = self.db.query(AnalysisJob).filter(AnalysisJob.status == status).count()
                job_stats[status] = count
            
            # Recent activity
            recent_jobs = self.db.query(AnalysisJob).filter(
                AnalysisJob.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            # Average job duration
            completed_jobs = self.db.query(AnalysisJob).filter(
                and_(
                    AnalysisJob.status == 'completed',
                    AnalysisJob.completed_at.isnot(None)
                )
            ).all()
            
            avg_duration = None
            if completed_jobs:
                durations = [
                    (job.completed_at - job.created_at).total_seconds()
                    for job in completed_jobs
                    if job.completed_at
                ]
                if durations:
                    avg_duration = sum(durations) / len(durations)
            
            stats = {
                'total_datasets': dataset_count,
                'total_jobs': sum(job_stats.values()),
                'jobs_by_status': job_stats,
                'recent_jobs_7_days': recent_jobs,
                'avg_job_duration_seconds': avg_duration,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            logger.info(
                "Database statistics generated successfully",
                total_datasets=dataset_count,
                total_jobs=sum(job_stats.values()),
                operation="database_stats"
            )
            
            return stats
            
        except Exception as e:
            logger.error(
                "Database statistics generation failed",
                error=str(e),
                operation="database_stats"
            )
            raise
    
    @monitor_performance("database_cleanup")
    @track_errors("database_operation")
    def cleanup_old_jobs(self, days_old: int = 30) -> int:
        """Clean up old completed/failed jobs with logging."""
        
        logger.info(
            "Starting database cleanup",
            days_old=days_old,
            operation="database_cleanup"
        )
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Count jobs to be deleted
            jobs_to_delete = self.db.query(AnalysisJob).filter(
                and_(
                    AnalysisJob.status.in_(['completed', 'failed']),
                    AnalysisJob.created_at < cutoff_date
                )
            ).count()
            
            if jobs_to_delete == 0:
                logger.info("No old jobs to clean up", operation="database_cleanup")
                return 0
            
            # Delete old jobs
            deleted_jobs = self.db.query(AnalysisJob).filter(
                and_(
                    AnalysisJob.status.in_(['completed', 'failed']),
                    AnalysisJob.created_at < cutoff_date
                )
            ).delete()
            
            self.db.commit()
            
            logger.info(
                "Database cleanup completed",
                deleted_jobs=deleted_jobs,
                cutoff_date=cutoff_date.isoformat(),
                operation="database_cleanup"
            )
            
            return deleted_jobs
            
        except Exception as e:
            logger.error(
                "Database cleanup failed",
                error=str(e),
                operation="database_cleanup"
            )
            self.db.rollback() 