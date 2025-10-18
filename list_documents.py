"""
Script to list all documents in the database
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from core.database import SessionLocal, Document
from sqlalchemy import desc

def list_all_documents(user_id: str):
    """
    List all documents for a user

    Args:
        user_id: User UUID
    """
    db = SessionLocal()
    try:
        # Get all documents for user, sorted by created_at descending
        all_docs = db.query(Document).filter_by(
            user_id=user_id
        ).order_by(desc(Document.created_at)).all()

        print(f"\n📊 Total documents for user {user_id}: {len(all_docs)}\n")

        if len(all_docs) == 0:
            print("✅ No documents found")
            return

        for idx, doc in enumerate(all_docs, 1):
            print(f"{idx}. ID: {doc.id}")
            print(f"   Filename: {doc.filename}")
            print(f"   Created: {doc.created_at}")
            print(f"   Status: {doc.status}")
            print(f"   Total chunks: {doc.total_chunks}")
            print()

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    USER_ID = "2d63181a-b335-4536-9501-f369d8ba0d9b"

    print(f"📋 Document List")
    print(f"   User ID: {USER_ID}")
    print(f"   Database: {os.getenv('DATABASE_URL', 'Not set')}")

    list_all_documents(USER_ID)
