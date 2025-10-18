"""
Simple script to call the R2 storage cleanup API endpoints
This script uses only the 'requests' library (standard Python)
"""
import requests
import sys

# Railway app URL
API_URL = "https://memvid-production.up.railway.app"

def check_r2_storage():
    """
    Check R2 storage usage - diagnose what's using space
    """
    endpoint = f"{API_URL}/api/admin/check-r2-storage"

    print(f"🔍 Check R2 Storage Usage")
    print(f"   Endpoint: {endpoint}")
    print("=" * 70)

    try:
        response = requests.get(
            endpoint,
            # Add your session cookie here if needed:
            # cookies={'session': 'your-session-cookie'}
        )

        if response.status_code == 401:
            print("❌ Not authenticated. Please:")
            print("   1. Open https://memvid-production.up.railway.app in your browser")
            print("   2. Log in with Telegram")
            print("   3. Copy your session cookie")
            print("   4. Add it to this script")
            return

        response.raise_for_status()
        result = response.json()

        print("\n✅ Storage Analysis:")
        print("=" * 70)

        summary = result.get('summary', {})
        print(f"   Total objects: {summary.get('total_objects', 0)}")
        print(f"   Current size: {summary.get('current_size_mb', 0)} MB")
        print(f"   Old versions: {summary.get('total_old_versions', 0)} ({summary.get('old_versions_size_mb', 0)} MB)")
        print(f"   Delete markers: {summary.get('total_delete_markers', 0)}")
        print(f"   Incomplete uploads: {summary.get('total_incomplete_uploads', 0)}")
        print(f"   TOTAL SIZE: {summary.get('total_size_mb', 0)} MB")

        recommendations = result.get('recommendations', [])
        if recommendations:
            print("\n⚠️  Issues Found:")
            for i, rec in enumerate(recommendations, 1):
                print(f"\n   {i}. {rec['issue']}")
                print(f"      Count: {rec.get('count', 0)}")
                if 'size_mb' in rec:
                    print(f"      Size: {rec['size_mb']} MB")
                print(f"      Solution: {rec['solution']}")
                print(f"      Action: {rec['action']}")

        print("\n" + "=" * 70)

    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling API: {e}")
        sys.exit(1)


def cleanup_orphaned_r2(dry_run=True):
    """
    Call the cleanup-orphaned-r2 endpoint

    Args:
        dry_run: If True, only show what would be deleted
    """
    endpoint = f"{API_URL}/api/admin/cleanup-orphaned-r2"

    print(f"🧹 Cleanup Orphaned R2 Files")
    print(f"   Endpoint: {endpoint}")
    print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE DELETE'}")
    print("=" * 70)

    try:
        response = requests.post(
            endpoint,
            json={"dry_run": dry_run},
            # Add your session cookie here if needed:
            # cookies={'session': 'your-session-cookie'}
        )

        if response.status_code == 401:
            print("❌ Not authenticated. Please:")
            print("   1. Open https://memvid-production.up.railway.app in your browser")
            print("   2. Log in with Telegram")
            print("   3. Copy your session cookie")
            print("   4. Add it to this script")
            return

        response.raise_for_status()
        result = response.json()

        print("\n✅ Response:")
        print(f"   Success: {result.get('success')}")
        print(f"   Message: {result.get('message')}")

        if 'orphaned_files' in result:
            print(f"\n   Orphaned files ({result.get('total_orphaned', 0)}):")
            for i, file in enumerate(result['orphaned_files'][:20], 1):
                print(f"     {i}. {file}")

            if result.get('total_orphaned', 0) > 20:
                print(f"     ... and {result['total_orphaned'] - 20} more files")

        if 'deleted_count' in result:
            print(f"\n   Deleted: {result.get('deleted_count')} files")
            print(f"   Failed: {result.get('failed_count', 0)} files")

        print("\n" + "=" * 70)

    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling API: {e}")
        sys.exit(1)


if __name__ == '__main__':
    # Parse command-line arguments
    if '--check' in sys.argv:
        check_r2_storage()
    elif '--cleanup' in sys.argv:
        dry_run = '--live' not in sys.argv

        if not dry_run:
            confirm = input("\n⚠️  WARNING: This will PERMANENTLY DELETE orphaned files!\n   Type 'yes' to confirm: ")
            if confirm.lower() != 'yes':
                print("Aborted.")
                sys.exit(0)

        cleanup_orphaned_r2(dry_run=dry_run)
    else:
        print("Usage:")
        print("  python run_cleanup_r2.py --check              # Check R2 storage usage")
        print("  python run_cleanup_r2.py --cleanup            # Dry run cleanup")
        print("  python run_cleanup_r2.py --cleanup --live     # Actually delete files")
