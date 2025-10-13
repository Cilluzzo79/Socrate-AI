"""
Database initialization script.
Run this script to create the database and tables.
"""

from pathlib import Path
import sys

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from database.models import init_db
from database.operations import sync_documents

if __name__ == "__main__":
    # Initialize the database
    engine = init_db()
    print("Database initialized successfully.")
    
    # Sync documents
    documents = sync_documents()
    print(f"Synchronized {len(documents)} documents.")
