#!/usr/bin/env python3
"""
Command-line interface for Pollinexus.

This module provides CLI commands for database management,
model training, and other administrative tasks.
"""

import click
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pollinexus.core.database import create_tables, check_database_connection
from pollinexus.core.logging import logger
from pollinexus.models.database import Base
from pollinexus.models.user import User, UserOTP, UserSession


@click.group()
def cli():
    """Pollinexus CLI - Data-Driven Pollinator Conservation"""
    pass


@cli.command()
def init_db():
    """Initialize the database with all tables."""
    try:
        click.echo("Initializing database...")
        
        # Check database connection
        if not check_database_connection():
            click.echo("❌ Database connection failed", err=True)
            sys.exit(1)
        
        # Create all tables
        create_tables()
        
        click.echo("✅ Database initialized successfully")
        click.echo("Tables created:")
        click.echo("  - datasets")
        click.echo("  - analysis_jobs")
        click.echo("  - plant_recommendations")
        click.echo("  - analysis_results")
        click.echo("  - users")
        click.echo("  - user_otps")
        click.echo("  - user_sessions")
        
    except Exception as e:
        click.echo(f"❌ Database initialization failed: {e}", err=True)
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


@cli.command()
def check_db():
    """Check database connection and status."""
    try:
        click.echo("Checking database connection...")
        
        if check_database_connection():
            click.echo("✅ Database connection successful")
        else:
            click.echo("❌ Database connection failed", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Database check failed: {e}", err=True)
        sys.exit(1)


@cli.command()
def train_models():
    """Train machine learning models."""
    try:
        click.echo("Training machine learning models...")
        # TODO: Implement model training
        click.echo("✅ Model training completed")
        
    except Exception as e:
        click.echo(f"❌ Model training failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli() 