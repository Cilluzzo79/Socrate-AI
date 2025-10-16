"""
Database migration script to remove file_data column from documents table.
This column was removed from the model but still exists in the PostgreSQL database.
"""

import os
import sys
from sqlalchemy import create_engine, text

def migrate_remove_file_data():
    """Remove file_data column from documents table"""

    # Get database URL
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False

    # Fix postgres:// to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    print(f"Connecting to database...")
    engine = create_engine(database_url)

    try:
        with engine.connect() as conn:
            # Check if column exists
            check_sql = text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='documents'
                AND column_name='file_data'
            """)

            result = conn.execute(check_sql)
            row = result.fetchone()

            if row:
                print("Found file_data column, removing it...")

                # Drop the column
                drop_sql = text("ALTER TABLE documents DROP COLUMN IF EXISTS file_data")
                conn.execute(drop_sql)
                conn.commit()

                print("✅ Successfully removed file_data column from documents table")
                return True
            else:
                print("ℹ️  file_data column not found, migration not needed")
                return True

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False
    finally:
        engine.dispose()

if __name__ == '__main__':
    print("=" * 60)
    print("DATABASE MIGRATION: Remove file_data column")
    print("=" * 60)

    success = migrate_remove_file_data()

    if success:
        print("\n✅ Migration completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Migration failed")
        sys.exit(1)
