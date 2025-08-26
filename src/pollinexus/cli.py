"""
Command line interface for Pollinexus.

This module provides CLI commands for database management and other utilities.
"""

import click
import logging
from pathlib import Path

from .core.database import create_tables, drop_tables, check_database_connection
from .services.duckdb_service import DuckDBService
from .core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Pollinexus CLI - Data-Driven Pollinator Conservation Platform"""
    pass


@cli.command()
def init_db():
    """Initialize the database by creating all tables."""
    click.echo("Initializing database...")
    try:
        create_tables()
        click.echo("✅ Database initialized successfully!")
    except Exception as e:
        click.echo(f"❌ Error initializing database: {e}")
        raise click.Abort()


@cli.command()
def drop_db():
    """Drop all database tables."""
    if click.confirm("Are you sure you want to drop all database tables?"):
        click.echo("Dropping database tables...")
        try:
            drop_tables()
            click.echo("✅ Database tables dropped successfully!")
        except Exception as e:
            click.echo(f"❌ Error dropping database tables: {e}")
            raise click.Abort()


@cli.command()
def check_db():
    """Check database connection."""
    click.echo("Checking database connection...")
    if check_database_connection():
        click.echo("✅ Database connection successful!")
    else:
        click.echo("❌ Database connection failed!")
        raise click.Abort()


@cli.command()
def create_upload_dir():
    """Create upload directory for datasets."""
    upload_dir = Path(settings.upload_dir)
    if upload_dir.exists():
        click.echo(f"Upload directory already exists: {upload_dir}")
    else:
        upload_dir.mkdir(parents=True, exist_ok=True)
        click.echo(f"✅ Created upload directory: {upload_dir}")


@cli.command()
@click.argument('csv_path', type=click.Path(exists=True))
@click.option('--table-name', '-t', help='Name for the table (defaults to filename)')
def load_csv(csv_path, table_name):
    """Load CSV file directly into DuckDB."""
    click.echo(f"Loading CSV file: {csv_path}")
    try:
        with DuckDBService() as db:
            table = db.load_csv_direct(csv_path, table_name)
            info = db.get_dataset_info(table)
            click.echo(f"✅ Loaded {info['total_rows']} rows into table '{table}'")
            click.echo(f"Columns: {len(info['columns'])}")
    except Exception as e:
        click.echo(f"❌ Error loading CSV: {e}")
        raise click.Abort()


@cli.command()
@click.argument('table_name')
def analyze_dataset(table_name):
    """Analyze dataset using DuckDB."""
    click.echo(f"Analyzing dataset: {table_name}")
    try:
        with DuckDBService() as db:
            analysis = db.analyze_bee_preferences(table_name)
            click.echo(f"✅ Analysis complete!")
            click.echo(f"Total observations: {analysis['summary']['total_observations']}")
            click.echo(f"Total bees: {analysis['summary']['total_bees']}")
            click.echo(f"Unique bee species: {analysis['summary']['unique_bee_species']}")
            click.echo(f"Unique plant species: {analysis['summary']['unique_plant_species']}")
    except Exception as e:
        click.echo(f"❌ Error analyzing dataset: {e}")
        raise click.Abort()


@cli.command()
@click.argument('table_name')
@click.option('--top-n', '-n', default=3, help='Number of recommendations to generate')
def get_recommendations(table_name, top_n):
    """Generate plant recommendations."""
    click.echo(f"Generating recommendations for table: {table_name}")
    try:
        with DuckDBService() as db:
            recommendations = db.get_plant_recommendations(table_name, top_n)
            click.echo(f"✅ Generated {len(recommendations)} recommendations:")
            for rec in recommendations:
                click.echo(f"  {rec['rank']}. {rec['plant_species']} (Score: {rec['score']:.3f})")
                click.echo(f"     {rec['reasoning']}")
    except Exception as e:
        click.echo(f"❌ Error generating recommendations: {e}")
        raise click.Abort()


@cli.command()
def setup():
    """Complete setup of the Pollinexus application."""
    click.echo("Setting up Pollinexus...")
    
    # Check database connection
    click.echo("1. Checking database connection...")
    if not check_database_connection():
        click.echo("❌ Database connection failed! Please check your configuration.")
        raise click.Abort()
    click.echo("✅ Database connection successful!")
    
    # Create upload directory
    click.echo("2. Creating upload directory...")
    upload_dir = Path(settings.upload_dir)
    if upload_dir.exists():
        click.echo(f"Upload directory already exists: {upload_dir}")
    else:
        upload_dir.mkdir(parents=True, exist_ok=True)
        click.echo(f"✅ Created upload directory: {upload_dir}")
    
    # Initialize database
    click.echo("3. Initializing database...")
    try:
        create_tables()
        click.echo("✅ Database initialized successfully!")
    except Exception as e:
        click.echo(f"❌ Error initializing database: {e}")
        raise click.Abort()
    
    click.echo("🎉 Pollinexus setup completed successfully!")


if __name__ == "__main__":
    cli() 