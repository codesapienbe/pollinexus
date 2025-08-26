#!/usr/bin/env python3
"""
Command-line interface for Pollinexus API.

This module provides CLI commands for database management,
data operations, and user management.
"""

import click
import os
from pathlib import Path
from sqlalchemy import text

from .core.database import get_db
from .core.config import settings
from .models.database import Base
from .models.user import User, UserOTP, UserSession
from .services.duckdb_service import DuckDBService
from .services.user_service import UserService


@click.group()
def cli():
    """Pollinexus API Command Line Interface."""
    pass


@cli.command()
def init_db():
    """Initialize the database with all tables."""
    try:
        db = next(get_db())
        
        # Create all tables
        Base.metadata.create_all(bind=db.bind)
        
        click.echo("✅ Database initialized successfully!")
        
    except Exception as e:
        click.echo(f"❌ Error initializing database: {e}")
        raise click.Abort()


@cli.command()
def create_upload_dir():
    """Create upload directory for file uploads."""
    try:
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        click.echo(f"✅ Upload directory created: {upload_dir.absolute()}")
        
    except Exception as e:
        click.echo(f"❌ Error creating upload directory: {e}")
        raise click.Abort()


@cli.command()
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--table-name', default='pollinator_data', help='Table name for the data')
def load_csv(csv_file, table_name):
    """Load CSV data into DuckDB."""
    try:
        service = DuckDBService()
        result = service.load_csv(csv_file, table_name)
        click.echo(f"✅ CSV loaded successfully: {result}")
        
    except Exception as e:
        click.echo(f"❌ Error loading CSV: {e}")
        raise click.Abort()


@cli.command()
@click.argument('table_name', default='pollinator_data')
def analyze_dataset(table_name):
    """Analyze a dataset in DuckDB."""
    try:
        service = DuckDBService()
        info = service.get_dataset_info(table_name)
        click.echo(f"✅ Dataset analysis: {info}")
        
    except Exception as e:
        click.echo(f"❌ Error analyzing dataset: {e}")
        raise click.Abort()


@cli.command()
@click.argument('table_name', default='pollinator_data')
def get_recommendations(table_name):
    """Get plant recommendations based on dataset."""
    try:
        service = DuckDBService()
        recommendations = service.generate_plant_recommendations(table_name)
        click.echo(f"✅ Plant recommendations: {recommendations}")
        
    except Exception as e:
        click.echo(f"❌ Error getting recommendations: {e}")
        raise click.Abort()


@cli.command()
@click.option('--full-name', prompt='Full name', help='User full name')
@click.option('--email', prompt='Email', help='User email address')
@click.option('--phone', prompt='Phone', help='User phone number')
@click.option('--password', prompt='Password', hide_input=True, help='User password')
@click.option('--role', default='user', help='User role (user/admin)')
def create_user(full_name, email, phone, password, role):
    """Create a new user account."""
    try:
        user = UserService.create_user(
            full_name=full_name,
            email=email,
            phone=phone,
            password=password
        )
        
        # Update role if specified
        if role != 'user':
            UserService.update_user(user["user_id"], role=role)
            user["role"] = role
        
        click.echo(f"✅ User created successfully!")
        click.echo(f"   User ID: {user['user_id']}")
        click.echo(f"   Name: {user['full_name']}")
        click.echo(f"   Email: {user['email']}")
        click.echo(f"   Role: {user['role']}")
        
    except Exception as e:
        click.echo(f"❌ Error creating user: {e}")
        raise click.Abort()


@cli.command()
@click.argument('email')
def get_user(email):
    """Get user information by email."""
    try:
        user = UserService.get_user_by_email(email)
        if user:
            click.echo(f"✅ User found:")
            click.echo(f"   User ID: {user['user_id']}")
            click.echo(f"   Name: {user['full_name']}")
            click.echo(f"   Email: {user['email']}")
            click.echo(f"   Phone: {user['phone']}")
            click.echo(f"   Role: {user['role']}")
            click.echo(f"   Verified: {user['is_verified']}")
            click.echo(f"   Created: {user['created_at']}")
        else:
            click.echo(f"❌ User not found: {email}")
        
    except Exception as e:
        click.echo(f"❌ Error getting user: {e}")
        raise click.Abort()


@cli.command()
@click.option('--page', default=1, help='Page number')
@click.option('--size', default=10, help='Page size')
def list_users(page, size):
    """List all users with pagination."""
    try:
        result = UserService.get_all_users(page=page, size=size)
        
        click.echo(f"✅ Users (Page {result['page']} of {(result['total'] + size - 1) // size}):")
        click.echo(f"   Total users: {result['total']}")
        click.echo(f"   Showing: {len(result['users'])} users")
        click.echo()
        
        for user in result['users']:
            click.echo(f"   ID: {user['id']}")
            click.echo(f"   Name: {user['first_name']} {user['last_name']}")
            click.echo(f"   Email: {user['email']}")
            click.echo(f"   Phone: {user['phone']}")
            click.echo(f"   Verified: {user['verified']}")
            click.echo(f"   Created: {user['created_at']}")
            click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error listing users: {e}")
        raise click.Abort()


@cli.command()
@click.argument('email')
@click.option('--full-name', help='New full name')
@click.option('--phone', help='New phone number')
@click.option('--role', help='New role')
@click.option('--verify/--unverify', help='Verify/unverify user')
def update_user(email, full_name, phone, role, verify):
    """Update user information."""
    try:
        user = UserService.get_user_by_email(email)
        if not user:
            click.echo(f"❌ User not found: {email}")
            return
        
        # Prepare update fields
        update_fields = {}
        if full_name:
            update_fields['full_name'] = full_name
        if phone:
            update_fields['phone'] = phone
        if role:
            update_fields['role'] = role
        if verify is not None:
            update_fields['is_verified'] = verify
        
        if not update_fields:
            click.echo("❌ No fields to update")
            return
        
        # Update user
        success = UserService.update_user(user['user_id'], **update_fields)
        
        if success:
            click.echo(f"✅ User updated successfully!")
            click.echo(f"   Updated fields: {', '.join(update_fields.keys())}")
        else:
            click.echo(f"❌ Error updating user")
        
    except Exception as e:
        click.echo(f"❌ Error updating user: {e}")
        raise click.Abort()


@cli.command()
@click.argument('email')
def delete_user(email):
    """Delete a user account (soft delete)."""
    try:
        user = UserService.get_user_by_email(email)
        if not user:
            click.echo(f"❌ User not found: {email}")
            return
        
        if click.confirm(f"Are you sure you want to delete user {email}?"):
            success = UserService.update_user(user['user_id'], is_deleted=True)
            
            if success:
                click.echo(f"✅ User deleted successfully!")
            else:
                click.echo(f"❌ Error deleting user")
        
    except Exception as e:
        click.echo(f"❌ Error deleting user: {e}")
        raise click.Abort()


@cli.command()
@click.argument('email')
def send_otp(email):
    """Send OTP to user email."""
    try:
        user = UserService.get_user_by_email(email)
        if not user:
            click.echo(f"❌ User not found: {email}")
            return
        
        otp = UserService.create_otp(user['user_id'], email=email)
        UserService.send_email_notification(user, "login_otp", otp=otp)
        
        click.echo(f"✅ OTP sent to {email}")
        click.echo(f"   OTP: {otp} (for testing purposes)")
        click.echo(f"   Expires in: 5 minutes")
        
    except Exception as e:
        click.echo(f"❌ Error sending OTP: {e}")
        raise click.Abort()


@cli.command()
def setup():
    """Complete setup of the application."""
    try:
        click.echo("🚀 Setting up Pollinexus API...")
        
        # Initialize database
        click.echo("📊 Initializing database...")
        init_db.callback()
        
        # Create upload directory
        click.echo("📁 Creating upload directory...")
        create_upload_dir.callback()
        
        # Create admin user
        click.echo("👤 Creating admin user...")
        if click.confirm("Do you want to create an admin user?"):
            create_user.callback(
                full_name="Admin User",
                email="admin@pollinexus.com",
                phone="+1234567890",
                password="admin123",
                role="admin"
            )
        
        click.echo("✅ Setup completed successfully!")
        
    except Exception as e:
        click.echo(f"❌ Setup failed: {e}")
        raise click.Abort()


if __name__ == '__main__':
    cli() 