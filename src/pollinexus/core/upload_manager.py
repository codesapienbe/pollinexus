"""
Upload manager for Pollinexus.

This module handles file uploads, path management, and file operations
with comprehensive logging and error handling.
"""

import os
import shutil
import time
from pathlib import Path
from typing import Optional, Tuple
import logging

from .config import settings
from .logging import logger


class UploadManager:
    """Manages file uploads and path operations."""
    
    def __init__(self):
        self.upload_dir = settings.get_upload_path()
        self._ensure_upload_directory()
        logger.info(
            "UploadManager initialized",
            extra={
                "upload_dir": str(self.upload_dir),
                "operation": "upload_manager_init"
            }
        )
    
    def _ensure_upload_directory(self) -> None:
        """Ensure upload directory exists and is writable."""
        try:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(
                "Upload directory ensured",
                extra={
                    "upload_dir": str(self.upload_dir),
                    "exists": self.upload_dir.exists(),
                    "is_dir": self.upload_dir.is_dir(),
                    "operation": "ensure_upload_directory"
                }
            )
        except Exception as e:
            logger.error(
                "Failed to create upload directory",
                extra={
                    "upload_dir": str(self.upload_dir),
                    "error": str(e),
                    "operation": "ensure_upload_directory"
                }
            )
            raise
    
    def get_absolute_path(self, file_path: str) -> Path:
        """Convert relative file path to absolute path."""
        path = Path(file_path)
        if path.is_absolute():
            return path
        
        # If it's a relative path, assume it's in the upload directory
        return self.upload_dir / path.name
    
    def save_uploaded_file(self, file, original_filename: str) -> Tuple[Path, str]:
        """
        Save uploaded file with unique filename.
        
        Args:
            file: Uploaded file object
            original_filename: Original filename
            
        Returns:
            Tuple of (file_path, checksum)
        """
        # Generate unique filename
        timestamp = int(time.time())
        sanitized_original = original_filename.replace(' ', '_')
        safe_filename = f"{timestamp}_{sanitized_original}"
        file_path = self.upload_dir / safe_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(
            "File saved successfully",
            extra={
                "original_filename": original_filename,
                "saved_filename": safe_filename,
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size if file_path.exists() else 0,
                "operation": "save_uploaded_file"
            }
        )
        
        return file_path, safe_filename
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists at given path."""
        absolute_path = self.get_absolute_path(file_path)
        exists = absolute_path.exists()
        
        logger.debug(
            "File existence check",
            extra={
                "original_path": file_path,
                "absolute_path": str(absolute_path),
                "exists": exists,
                "operation": "file_exists"
            }
        )
        
        return exists
    
    def get_file_info(self, file_path: str) -> dict:
        """Get file information."""
        absolute_path = self.get_absolute_path(file_path)
        
        if not absolute_path.exists():
            return {
                "exists": False,
                "path": str(absolute_path),
                "size": 0,
                "error": "File not found"
            }
        
        try:
            stat = absolute_path.stat()
            return {
                "exists": True,
                "path": str(absolute_path),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "error": None
            }
        except Exception as e:
            logger.error(
                "Failed to get file info",
                extra={
                    "file_path": str(absolute_path),
                    "error": str(e),
                    "operation": "get_file_info"
                }
            )
            return {
                "exists": False,
                "path": str(absolute_path),
                "size": 0,
                "error": str(e)
            }
    
    def cleanup_file(self, file_path: str) -> bool:
        """Clean up file if it exists."""
        absolute_path = self.get_absolute_path(file_path)
        
        if absolute_path.exists():
            try:
                absolute_path.unlink()
                logger.info(
                    "File cleaned up successfully",
                    extra={
                        "file_path": str(absolute_path),
                        "operation": "cleanup_file"
                    }
                )
                return True
            except Exception as e:
                logger.error(
                    "Failed to cleanup file",
                    extra={
                        "file_path": str(absolute_path),
                        "error": str(e),
                        "operation": "cleanup_file"
                    }
                )
                return False
        
        return True


# Global upload manager instance
upload_manager = UploadManager() 