#!/usr/bin/env python3
"""
Basic API Test Script
Tests the core API endpoints without requiring Telegram auth
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import os
os.environ['DATABASE_URL'] = 'sqlite:///socrate_ai_dev.db'
os.environ['SECRET_KEY'] = 'test-key'

from core.database import get_or_create_user, SessionLocal
from core.document_operations import create_document, get_user_documents, get_user_stats

def test_database_operations():
    """Test basic database operations"""
    print("=" * 60)
    print("Testing Database Operations")
    print("=" * 60)

    # Test 1: Create user
    print("\n[1] Creating test user...")
    user = get_or_create_user(
        telegram_id=12345678,
        first_name="Test",
        last_name="User",
        username="testuser"
    )
    print(f"    User created: {user.first_name} (ID: {user.id})")

    # Test 2: Create document
    print("\n[2] Creating test document...")
    doc = create_document(
        user_id=str(user.id),
        filename="test_document.pdf",
        file_path="/fake/path/test.pdf",
        file_size=1024000,  # 1 MB
        mime_type="application/pdf"
    )
    print(f"    Document created: {doc.filename} (ID: {doc.id})")
    print(f"    Status: {doc.status}")

    # Test 3: List user documents
    print("\n[3] Listing user documents...")
    docs = get_user_documents(str(user.id))
    print(f"    Found {len(docs)} documents")
    for d in docs:
        print(f"      - {d.filename} ({d.status})")

    # Test 4: Get user stats
    print("\n[4] Getting user statistics...")
    stats = get_user_stats(str(user.id))
    print(f"    Storage used: {stats['user']['storage_used_mb']} MB")
    print(f"    Storage quota: {stats['user']['storage_quota_mb']} MB")
    print(f"    Total documents: {stats['documents']['total']}")
    print(f"    Total chat sessions: {stats['chat_sessions']['total']}")

    print("\n" + "=" * 60)
    print("[OK] All database tests passed!")
    print("=" * 60)

    return user, doc

def test_api_server():
    """Test that API server can start"""
    print("\n\n" + "=" * 60)
    print("Testing API Server")
    print("=" * 60)

    try:
        from api_server import app
        print("\n[OK] API server module loaded successfully")
        print(f"    Routes registered: {len(app.url_map._rules)}")

        # List some routes
        print("\n[Routes]")
        for rule in list(app.url_map.iter_rules())[:10]:
            print(f"    {rule.methods} {rule.rule}")

        print("\n" + "=" * 60)
        print("[OK] API server ready")
        print("=" * 60)

        return app

    except Exception as e:
        print(f"\n[ERROR] Failed to load API server: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print(" " * 20 + "SOCRATE AI - API TEST")
    print("=" * 70)

    # Test database
    user, doc = test_database_operations()

    # Test API
    app = test_api_server()

    if app:
        print("\n\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Configure TELEGRAM_BOT_TOKEN in .env")
        print("  2. Run: python api_server.py")
        print("  3. Open: http://localhost:5000")
        print("=" * 70 + "\n")
    else:
        print("\n[ERROR] Some tests failed")
        sys.exit(1)
