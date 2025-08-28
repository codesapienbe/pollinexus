#!/usr/bin/env python3
"""
Command-line interface for Pollinexus.

This module provides CLI commands for development, testing, and deployment.
"""

import click
import subprocess
import sys
import platform
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from .core.config import settings
from .core.logging import logger


@click.group()
def cli():
    """Pollinexus CLI - Development and deployment tools."""
    pass


@cli.command()
def setup():
    """Setup local development environment."""
    click.echo("🚀 Pollinexus Local Development Setup")
    click.echo("=" * 50)
    
    # Check if Redis is already running
    if check_redis():
        click.echo("\n🎉 Redis is already set up! You can start the API.")
        return
    
    # Install Redis Python package
    click.echo("\n📦 Installing Redis Python package...")
    if not install_redis_package():
        click.echo("❌ Failed to install Redis Python package")
        sys.exit(1)
    
    # Try to start Redis
    click.echo("\n🔧 Setting up Redis...")
    
    # Try Docker first
    click.echo("Trying Docker...")
    if start_redis_docker():
        if check_redis():
            click.echo("\n🎉 Redis setup complete! You can start the API.")
            return
    
    # Try system installation
    click.echo("Trying system installation...")
    if install_redis_system():
        if check_redis():
            click.echo("\n🎉 Redis setup complete! You can start the API.")
            return
    
    # Fallback message
    click.echo("\n⚠️  Redis setup incomplete. The API will work with synchronous tasks.")
    click.echo("   To enable background tasks, install Redis manually:")
    click.echo("   - Windows: Download from GitHub releases")
    click.echo("   - macOS: brew install redis")
    click.echo("   - Linux: sudo apt-get install redis-server")
    click.echo("   - Or use Docker: docker run -d -p 6379:6379 redis:7-alpine")


def check_redis():
    """Check if Redis is available."""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        click.echo("✅ Redis is running and accessible")
        return True
    except ImportError:
        click.echo("❌ Redis Python package not installed")
        return False
    except Exception as e:
        click.echo(f"❌ Redis not accessible: {e}")
        return False


def install_redis_package():
    """Install Redis Python package."""
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "redis"], check=True)
        click.echo("✅ Redis Python package installed")
        return True
    except subprocess.CalledProcessError:
        click.echo("❌ Failed to install Redis Python package")
        return False


def start_redis_docker():
    """Start Redis using Docker."""
    try:
        # Check if Docker is available
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        
        # Start Redis container
        subprocess.run([
            "docker", "run", "-d", "--name", "pollinexus-redis",
            "-p", "6379:6379", "redis:7-alpine"
        ], check=True)
        
        click.echo("✅ Redis started using Docker")
        return True
    except subprocess.CalledProcessError:
        click.echo("❌ Failed to start Redis with Docker")
        return False
    except FileNotFoundError:
        click.echo("❌ Docker not found")
        return False


def install_redis_system():
    """Install Redis on the system."""
    system = platform.system().lower()
    
    if system == "windows":
        click.echo("📝 For Windows, please install Redis manually:")
        click.echo("   1. Download from: https://github.com/microsoftarchive/redis/releases")
        click.echo("   2. Or use WSL2 with Ubuntu")
        return False
    elif system == "darwin":  # macOS
        try:
            subprocess.run(["brew", "install", "redis"], check=True)
            subprocess.run(["brew", "services", "start", "redis"], check=True)
            click.echo("✅ Redis installed and started via Homebrew")
            return True
        except subprocess.CalledProcessError:
            click.echo("❌ Failed to install Redis via Homebrew")
            return False
    elif system == "linux":
        try:
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "redis-server"], check=True)
            subprocess.run(["sudo", "systemctl", "start", "redis-server"], check=True)
            click.echo("✅ Redis installed and started via apt")
            return True
        except subprocess.CalledProcessError:
            click.echo("❌ Failed to install Redis via apt")
            return False
    else:
        click.echo(f"❌ Unsupported system: {system}")
        return False


@cli.command()
def run():
    """Run the Pollinexus API server."""
    import uvicorn
    import asyncio
    from .core.shutdown import shutdown_manager
    
    click.echo("🚀 Starting Pollinexus API...")
    click.echo("📝 Press Ctrl+C for graceful shutdown")
    
    try:
        uvicorn.run(
            "pollinexus.api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=settings.reload,
            log_level=settings.log_level.lower()
        )
    except KeyboardInterrupt:
        # In development, exit immediately to allow hot reload
        if settings.is_development or settings.reload:
            click.echo("\n🛑 Development stop detected. Exiting immediately for hot reload...")
            sys.exit(0)
        
        click.echo("\n🛑 Graceful shutdown requested...")
        
        # Perform graceful shutdown (non-development)
        if asyncio.get_event_loop().is_running():
            asyncio.get_event_loop().run_until_complete(
                shutdown_manager.perform_graceful_shutdown()
            )
        else:
            # Create new event loop if needed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    shutdown_manager.perform_graceful_shutdown()
                )
            finally:
                loop.close()
        
        click.echo("✅ Graceful shutdown completed")
    except Exception as e:
        click.echo(f"❌ Application error: {e}")
        sys.exit(1)


@cli.command()
def test():
    """Run tests."""
    click.echo("🧪 Running tests...")
    
    # Run pytest
    try:
        subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], check=True)
        click.echo("✅ Tests passed!")
    except subprocess.CalledProcessError:
        click.echo("❌ Tests failed!")
        sys.exit(1)


@cli.command()
def lint():
    """Run linting."""
    click.echo("🔍 Running linting...")
    
    try:
        subprocess.run([sys.executable, "-m", "flake8", "src/"], check=True)
        click.echo("✅ Linting passed!")
    except subprocess.CalledProcessError:
        click.echo("❌ Linting failed!")
        sys.exit(1)


@cli.command()
def format():
    """Format code."""
    click.echo("🎨 Formatting code...")
    
    try:
        subprocess.run([sys.executable, "-m", "black", "src/"], check=True)
        subprocess.run([sys.executable, "-m", "isort", "src/"], check=True)
        click.echo("✅ Code formatted!")
    except subprocess.CalledProcessError:
        click.echo("❌ Code formatting failed!")
        sys.exit(1)


if __name__ == "__main__":
    cli() 