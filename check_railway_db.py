"""
Quick script to check Railway database for documents
"""
import psycopg2

# Railway PostgreSQL connection
DATABASE_URL = "postgresql://postgres:tjFSedoKaPrYjprEdSknSoDoFTamuohV@hopper.proxy.rlwy.net:30086/railway"
USER_ID = "2d63181a-b335-4536-9501-f369d8ba0d9b"

print("=" * 80)
print("RAILWAY DATABASE CHECK")
print("=" * 80)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Check if documents table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'documents'
        );
    """)
    table_exists = cursor.fetchone()[0]

    if not table_exists:
        print("\nTables do NOT exist in database!")
        print("Database was reset but web service may not have recreated tables yet.")
        cursor.close()
        conn.close()
        exit(1)

    # Count total documents
    cursor.execute("SELECT COUNT(*) FROM documents WHERE user_id = %s", (USER_ID,))
    total_docs = cursor.fetchone()[0]

    print(f"\nTotal documents for user: {total_docs}\n")

    if total_docs == 0:
        print("NO DOCUMENTS FOUND IN DATABASE!")
        print("\nThis means:")
        print("  1. Database was reset successfully")
        print("  2. User has NOT uploaded any new documents since reset")
        print("  3. That's why queries are failing with 502 error!")
        print("\n" + "=" * 80)
        cursor.close()
        conn.close()
        exit(0)

    # List all documents
    cursor.execute("""
        SELECT id, filename, status, created_at, total_chunks
        FROM documents
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (USER_ID,))

    docs = cursor.fetchall()

    for idx, (doc_id, filename, status, created_at, total_chunks) in enumerate(docs, 1):
        print(f"{idx}. ID: {doc_id}")
        print(f"   Filename: {filename}")
        print(f"   Status: {status}")
        print(f"   Created: {created_at}")
        print(f"   Chunks: {total_chunks}")
        print()

    cursor.close()
    conn.close()

    print("=" * 80)

except Exception as e:
    print(f"\nERROR: {e}")
    exit(1)
