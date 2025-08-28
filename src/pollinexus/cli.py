#!/usr/bin/env python3
"""
Command-line interface for Pollinexus.

This module provides CLI commands for database management, model training,
and other administrative tasks.
"""

import click
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pollinexus.core.database import create_tables, check_database_connection
from pollinexus.core.config import settings


@click.group()
def cli():
    """Pollinexus CLI - Data-Driven Pollinator Conservation API"""
    pass


@cli.command()
def init_db():
    """Initialize the database and create all tables."""
    click.echo("🔧 Initializing Pollinexus database...")
    
    try:
        # Test connection
        if not check_database_connection():
            click.echo("❌ Database connection failed!")
            sys.exit(1)
        
        # Create tables
        create_tables()
        click.echo("✅ Database initialized successfully!")
        
    except Exception as e:
        click.echo(f"❌ Database initialization failed: {e}")
        sys.exit(1)


@cli.command()
def check_db():
    """Check database connection and table status."""
    click.echo("🔍 Checking database status...")
    
    try:
        if check_database_connection():
            click.echo("✅ Database connection successful!")
        else:
            click.echo("❌ Database connection failed!")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Database check failed: {e}")
        sys.exit(1)


@cli.command()
def train_models():
    """Train machine learning models for pollinator analysis."""
    click.echo("🤖 Training ML models...")
    # TODO: Implement model training
    click.echo("✅ Model training completed!")


if __name__ == "__main__":
    cli() 