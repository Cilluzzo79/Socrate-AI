"""
Simple database reset script - connects to Railway PostgreSQL and drops all tables
"""
import os

# Railway PostgreSQL connection string
DATABASE_URL = "postgresql://postgres:tjFSedoKaPrYjprEdSknSoDoFTamuohV@hopper.proxy.rlwy.net:30086/railway"

print("=" * 80)
print("DATABASE RESET SCRIPT")
print("=" * 80)
print(f"Target: Railway PostgreSQL")
print("WARNING: This will DELETE ALL DATA!")
print("=" * 80)

response = input("\nType 'YES' to confirm reset: ")

if response != 'YES':
    print("❌ Reset cancelled")
    exit(0)

try:
    import psycopg2

    print("\n🔌 Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()

    print("🗑️  Dropping all tables...")

    cursor.execute("DROP TABLE IF EXISTS chat_sessions CASCADE;")
    print("   ✅ Dropped: chat_sessions")

    cursor.execute("DROP TABLE IF EXISTS documents CASCADE;")
    print("   ✅ Dropped: documents")

    cursor.execute("DROP TABLE IF EXISTS users CASCADE;")
    print("   ✅ Dropped: users")

    cursor.close()
    conn.close()

    print("\n✅ Database reset completed!")
    print("📝 Tables will be recreated on next API startup via init_db()")
    print("\n" + "=" * 80)

except ImportError:
    print("\n❌ ERROR: psycopg2 not installed")
    print("Install it with: pip install psycopg2-binary")
    exit(1)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    exit(1)
