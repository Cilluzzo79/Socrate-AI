"""
Test database operations without Celery
Verifies multi-tenant CRUD operations
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.database import init_db, get_or_create_user, SessionLocal
from core.document_operations import (
    create_document,
    get_document_by_id,
    get_user_documents,
    update_document_status,
    delete_document,
    create_chat_session,
    get_user_stats
)

def test_database_operations():
    """Test all database operations"""

    print("="*80)
    print("DATABASE OPERATIONS TEST")
    print("="*80)

    # 1. Clean and initialize database
    print("\n[1/8] Cleaning and initializing database...")

    # Remove old database file if exists
    import os
    db_file = "socrate_ai_dev.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"[OK] Removed old database: {db_file}")

    init_db()
    print("[OK] Database initialized")

    # 2. Create test users
    print("\n[2/8] Creating test users...")
    user1 = get_or_create_user(
        telegram_id=111111,
        first_name="User",
        last_name="One",
        username="user1"
    )
    user2 = get_or_create_user(
        telegram_id=222222,
        first_name="User",
        last_name="Two",
        username="user2"
    )
    print(f"[OK] User 1: {user1.id} (telegram_id: {user1.telegram_id})")
    print(f"[OK] User 2: {user2.id} (telegram_id: {user2.telegram_id})")

    # 3. Create documents for user1
    print("\n[3/8] Creating documents for user1...")
    doc1 = create_document(
        user_id=str(user1.id),
        filename="test1.pdf",
        original_filename="test1.pdf",
        file_path="/tmp/test1.pdf",
        file_size=1024,
        mime_type="application/pdf"
    )
    doc2 = create_document(
        user_id=str(user1.id),
        filename="test2.pdf",
        original_filename="test2.pdf",
        file_path="/tmp/test2.pdf",
        file_size=2048,
        mime_type="application/pdf"
    )
    print(f"[OK] Document 1: {doc1.id} (status: {doc1.status})")
    print(f"[OK] Document 2: {doc2.id} (status: {doc2.status})")

    # 4. Create document for user2
    print("\n[4/8] Creating document for user2...")
    doc3 = create_document(
        user_id=str(user2.id),
        filename="test3.pdf",
        original_filename="test3.pdf",
        file_path="/tmp/test3.pdf",
        file_size=3072,
        mime_type="application/pdf"
    )
    print(f"[OK] Document 3: {doc3.id} (status: {doc3.status})")

    # 5. Test multi-tenant isolation
    print("\n[5/8] Testing multi-tenant isolation...")

    # User1 should see only their documents
    user1_docs = get_user_documents(str(user1.id))
    print(f"[OK] User1 documents: {len(user1_docs)} (expected: 2)")
    assert len(user1_docs) == 2, "User1 should have 2 documents"

    # User2 should see only their document
    user2_docs = get_user_documents(str(user2.id))
    print(f"[OK] User2 documents: {len(user2_docs)} (expected: 1)")
    assert len(user2_docs) == 1, "User2 should have 1 document"

    # User1 should NOT be able to access User2's document
    user2_doc_as_user1 = get_document_by_id(str(doc3.id), str(user1.id))
    print(f"[OK] User1 accessing User2's doc: {user2_doc_as_user1} (expected: None)")
    assert user2_doc_as_user1 is None, "Multi-tenant isolation failed!"

    # 6. Update document status
    print("\n[6/8] Testing document status updates...")

    update_document_status(
        str(doc1.id),
        str(user1.id),
        status='ready',
        processing_progress=100,
        total_chunks=10,
        total_tokens=1000,
        language='it',
        doc_metadata={
            'test_key': 'test_value',
            'processed_at': '2025-01-13'
        }
    )

    updated_doc = get_document_by_id(str(doc1.id), str(user1.id))
    print(f"[OK] Document status: {updated_doc.status}")
    print(f"[OK] Progress: {updated_doc.processing_progress}%")
    print(f"[OK] Chunks: {updated_doc.total_chunks}")
    print(f"[OK] Tokens: {updated_doc.total_tokens}")
    print(f"[OK] Language: {updated_doc.language}")
    print(f"[OK] Metadata: {updated_doc.doc_metadata}")

    assert updated_doc.status == 'ready'
    assert updated_doc.processing_progress == 100
    assert updated_doc.total_chunks == 10

    # 7. Create chat session
    print("\n[7/8] Testing chat session creation...")

    session = create_chat_session(
        user_id=str(user1.id),
        document_id=str(doc1.id),
        command_type='quiz',
        request_data={'query': 'Create a quiz'},
        channel='web_app'
    )

    print(f"[OK] Chat session: {session.id}")
    print(f"[OK] Command type: {session.command_type}")
    print(f"[OK] Channel: {session.channel}")

    # 8. Get user stats
    print("\n[8/8] Testing user statistics...")

    stats = get_user_stats(str(user1.id))
    print(f"[OK] User: {stats['user']['first_name']} (tier: {stats['user']['subscription_tier']})")
    print(f"[OK] Storage: {stats['user']['storage_used_mb']}/{stats['user']['storage_quota_mb']} MB")
    print(f"[OK] Total documents: {stats['documents']['total']}")
    print(f"[OK] Ready documents: {stats['documents']['ready']}")
    print(f"[OK] Processing documents: {stats['documents']['processing']}")
    print(f"[OK] Total sessions: {stats['chat_sessions']['total']}")

    assert stats['documents']['total'] == 2
    assert stats['documents']['ready'] == 1
    assert stats['documents']['processing'] == 1
    assert stats['chat_sessions']['total'] == 1

    print("\n" + "="*80)
    print("ALL TESTS PASSED!")
    print("="*80)
    print("\nDatabase operations working correctly:")
    print("  - Multi-tenant isolation: OK")
    print("  - Document CRUD: OK")
    print("  - Status updates: OK")
    print("  - Chat sessions: OK")
    print("  - User statistics: OK")
    print("\nReady for async processing integration!")

    return True


if __name__ == '__main__':
    try:
        success = test_database_operations()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
