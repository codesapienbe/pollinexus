"""
API routes package for Pollinexus.

This package contains FastAPI route definitions for different API endpoints.
"""

from . import datasets, analysis, visualizations

__all__ = ["datasets", "analysis", "visualizations"] 