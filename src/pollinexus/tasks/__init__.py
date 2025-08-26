"""
Celery tasks package for Pollinexus.

This package contains background task definitions for data analysis,
visualization, and report generation.
"""

from .celery_app import celery_app

__all__ = ["celery_app"] 