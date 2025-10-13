#!/usr/bin/env python3
"""
Database Initialization Script
Run this to create all tables in the database
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.database import init_db, reset_db
import os

def main():
    """Main initialization function"""
    print("=" * 60)
    print("Socrate AI - Database Initialization")
    print("=" * 60)

    # Check database URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("\n[!] WARNING: DATABASE_URL not set in environment")
        print("    Using default SQLite database")
        db_url = "sqlite:///socrate_ai_dev.db"
        os.environ['DATABASE_URL'] = db_url

    print(f"\n[DB] Database: {db_url.split('@')[0]}...")  # Hide password

    # Ask for confirmation if resetting
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        print("\n[!] RESET MODE: This will DELETE all existing data!")
        response = input("    Are you sure? (yes/no): ")

        if response.lower() != 'yes':
            print("\n[X] Reset cancelled")
            return

        print("\n[~] Resetting database...")
        success = reset_db()

        if success:
            print("[OK] Database reset successfully!")
        else:
            print("[ERROR] Database reset failed")
            sys.exit(1)
    else:
        print("\n[~] Initializing database...")
        success = init_db()

        if success:
            print("\n[OK] Database initialized successfully!")
            print("\n[Tables created]")
            print("    - users")
            print("    - documents")
            print("    - chat_sessions")
        else:
            print("\n[ERROR] Database initialization failed")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("Next steps:")
    print("  1. Configure .env file with your credentials")
    print("  2. Run: python api_server.py")
    print("  3. Open http://localhost:5000 in browser")
    print("=" * 60)

if __name__ == '__main__':
    main()
