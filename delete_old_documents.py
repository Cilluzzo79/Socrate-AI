"""
Delete all documents except the most recent one
This script runs DIRECTLY on Railway
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from core.database import SessionLocal, Document
from sqlalchemy import desc

def delete_old_documents(user_id: str):
    """
    Delete all documents except the most recent one

    Args:
        user_id: User UUID
    """
    db = SessionLocal()
    try:
        # Get all documents for user, sorted by created_at descending
        all_docs = db.query(Document).filter_by(
            user_id=user_id
        ).order_by(desc(Document.created_at)).all()

        print(f"\nTotal documents for user {user_id}: {len(all_docs)}")

        if len(all_docs) <= 1:
            print(f"Only {len(all_docs)} document(s) found, nothing to delete")
            return

        # Keep latest, delete the rest
        doc_to_keep = all_docs[0]
        docs_to_delete = all_docs[1:]

        print(f"\nKeeping LATEST document:")
        print(f"  - ID: {doc_to_keep.id}")
        print(f"  - Filename: {doc_to_keep.filename}")
        print(f"  - Created: {doc_to_keep.created_at}")
        print(f"  - Status: {doc_to_keep.status}")
        print(f"  - Chunks: {doc_to_keep.total_chunks}")

        print(f"\nDeleting {len(docs_to_delete)} OLD document(s):")
        for doc in docs_to_delete:
            print(f"  - ID: {doc.id}")
            print(f"    Filename: {doc.filename}")
            print(f"    Created: {doc.created_at}")
            print(f"    Status: {doc.status}")
            print(f"    Chunks: {doc.total_chunks}")

        # Delete old documents
        deleted_count = 0
        for doc in docs_to_delete:
            try:
                db.delete(doc)
                deleted_count += 1
                print(f"\nDeleted: {doc.id}")
            except Exception as e:
                print(f"\nError deleting {doc.id}: {e}")

        db.commit()
        print(f"\nSuccessfully deleted {deleted_count} document(s)")
        print(f"Remaining documents: 1")

    except Exception as e:
        print(f"\nError: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    USER_ID = "2d63181a-b335-4536-9501-f369d8ba0d9b"

    print("=" * 80)
    print("DELETE OLD DOCUMENTS SCRIPT")
    print("=" * 80)
    print(f"User ID: {USER_ID}")
    print(f"Database: {os.getenv('DATABASE_URL', 'Not set')[:50]}...")
    print("=" * 80)

    delete_old_documents(USER_ID)

    print("\n" + "=" * 80)
    print("CLEANUP COMPLETED")
    print("=" * 80)
