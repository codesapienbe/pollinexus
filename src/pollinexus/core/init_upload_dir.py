"""
Upload directory initialization script.

This script ensures the upload directory is properly created and configured
for the Pollinexus application.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.pollinexus.core.config import settings
from src.pollinexus.core.logging import logger


def init_upload_directory():
    """Initialize the upload directory with proper permissions."""
    try:
        # Get upload path
        upload_path = settings.get_upload_path()
        
        # Create directory if it doesn't exist
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # Test write permissions
        test_file = upload_path / ".test_write"
        test_file.write_text("test")
        test_file.unlink()
        
        logger.info(
            "Upload directory initialized successfully",
            extra={
                "upload_path": str(upload_path),
                "exists": upload_path.exists(),
                "is_dir": upload_path.is_dir(),
                "writable": True,
                "operation": "init_upload_directory"
            }
        )
        
        print(f"✅ Upload directory initialized: {upload_path}")
        return True
        
    except Exception as e:
        logger.error(
            "Failed to initialize upload directory",
            extra={
                "error": str(e),
                "operation": "init_upload_directory"
            }
        )
        
        print(f"❌ Failed to initialize upload directory: {e}")
        return False


if __name__ == "__main__":
    success = init_upload_directory()
    sys.exit(0 if success else 1) 