"""
Initialization script for the Memvid Chat system.
Run this script to initialize the environment, database, and documents.

Usage:
    python initialize.py
"""

import os
import sys
from pathlib import Path
import argparse

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import local modules
from utils.helpers import initialize_project_directories
from database.models import init_db
from database.operations import sync_documents
from config.config import validate_env_vars


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Initialize the Memvid Chat system.")
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-initialization even if already initialized."
    )
    return parser.parse_args()


def initialize_system(force=False):
    """
    Initialize the system.
    
    Args:
        force: Force re-initialization even if already initialized.
        
    Returns:
        bool: Success status
    """
    # Check if already initialized
    db_path = project_root / "database" / "conversations.db"
    if db_path.exists() and not force:
        print("Database already exists. Use --force to reinitialize.")
        return True
    
    # Initialize project directories
    try:
        print("Initializing project directories...")
        initialize_project_directories()
        print("Project directories initialized successfully.")
    except Exception as e:
        print(f"ERROR: Failed to initialize project directories: {e}")
        return False
    
    # Validate environment variables
    missing_vars = validate_env_vars()
    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in the .env file or environment.")
        return False
    
    # Initialize database
    try:
        print("Initializing database...")
        engine = init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"ERROR: Failed to initialize database: {e}")
        return False
    
    # Sync documents
    try:
        print("Synchronizing documents...")
        documents = sync_documents()
        print(f"Synchronized {len(documents)} documents.")
    except Exception as e:
        print(f"ERROR: Failed to synchronize documents: {e}")
        return False
    
    return True


if __name__ == "__main__":
    args = parse_args()
    
    print("Initializing Memvid Chat system...")
    if initialize_system(args.force):
        print("Initialization completed successfully.")
        print("To start the bot, run: python main.py")
    else:
        print("Initialization failed. Please check the error messages above.")
        sys.exit(1)
