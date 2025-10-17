"""
Cleanup script to delete all old documents except the latest one
RUN THIS CAREFULLY - it will delete data!
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from core.database import SessionLocal, Document
from sqlalchemy import desc

def cleanup_old_documents(user_id: str, keep_latest: int = 1):
    """
    Delete all documents except the latest N

    Args:
        user_id: User UUID
        keep_latest: Number of latest documents to keep
    """
    db = SessionLocal()
    try:
        # Get all documents for user, sorted by created_at descending
        all_docs = db.query(Document).filter_by(
            user_id=user_id
        ).order_by(desc(Document.created_at)).all()

        print(f"\n📊 Total documents for user {user_id}: {len(all_docs)}")

        if len(all_docs) <= keep_latest:
            print(f"✅ Only {len(all_docs)} documents found, nothing to delete")
            return

        # Keep latest N, delete the rest
        docs_to_keep = all_docs[:keep_latest]
        docs_to_delete = all_docs[keep_latest:]

        print(f"\n✅ Keeping {len(docs_to_keep)} latest documents:")
        for doc in docs_to_keep:
            print(f"   - {doc.id} | {doc.filename} | {doc.created_at}")

        print(f"\n⚠️  Deleting {len(docs_to_delete)} old documents:")
        for doc in docs_to_delete:
            print(f"   - {doc.id} | {doc.filename} | {doc.created_at}")

        # Ask for confirmation
        response = input(f"\n❓ Delete {len(docs_to_delete)} documents? (yes/no): ")

        if response.lower() != 'yes':
            print("❌ Aborted")
            return

        # Delete old documents
        deleted_count = 0
        for doc in docs_to_delete:
            try:
                db.delete(doc)
                deleted_count += 1
                print(f"   ✅ Deleted: {doc.id}")
            except Exception as e:
                print(f"   ❌ Error deleting {doc.id}: {e}")

        db.commit()
        print(f"\n✅ Successfully deleted {deleted_count} documents")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # MODIFY THIS to your user_id
    USER_ID = "2d63181a-b335-4536-9501-f369d8ba0d9b"

    print(f"🧹 Cleanup Old Documents Script")
    print(f"   User ID: {USER_ID}")
    print(f"   Keeping: Latest 1 document")
    print(f"   Database: {os.getenv('DATABASE_URL', 'Not set')}")

    cleanup_old_documents(USER_ID, keep_latest=1)
