"""
Core functionality package for Pollinexus.

This package contains core components like configuration, database connections,
and shared utilities.
"""

from .config import Settings
from .database import get_db, Base

__all__ = ["Settings", "get_db", "Base"] 