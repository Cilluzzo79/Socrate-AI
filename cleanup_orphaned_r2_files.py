"""
Cleanup Orphaned R2 Files
--------------------------
This script identifies and deletes files on Cloudflare R2 that no longer have
corresponding database records (orphaned after incomplete deletions).

Usage:
    python cleanup_orphaned_r2_files.py --dry-run  # Preview what will be deleted
    python cleanup_orphaned_r2_files.py            # Actually delete orphaned files
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Set, List, Dict

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from core.database import SessionLocal, Document
from core.s3_storage import list_r2_files, delete_file, R2_BUCKET_NAME

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_valid_r2_keys_from_db() -> Set[str]:
    """
    Get all R2 keys that are referenced in the database

    Returns:
        Set of R2 keys that should exist
    """
    db = SessionLocal()
    valid_keys = set()

    try:
        # Get all documents
        documents = db.query(Document).all()
        logger.info(f"Found {len(documents)} documents in database")

        for doc in documents:
            # 1. Original file (PDF/document)
            if doc.file_path and '/' in doc.file_path:
                valid_keys.add(doc.file_path)

            # 2. Metadata JSON
            if doc.doc_metadata:
                metadata_r2_key = doc.doc_metadata.get('metadata_r2_key')
                if metadata_r2_key and metadata_r2_key != 'inline' and '/' in metadata_r2_key:
                    valid_keys.add(metadata_r2_key)

                # 3. Video file
                video_r2_key = doc.doc_metadata.get('video_r2_key')
                if video_r2_key and '/' in video_r2_key:
                    valid_keys.add(video_r2_key)

                # 4. Embeddings file (if separate)
                embeddings_r2_key = doc.doc_metadata.get('embeddings_r2_key')
                if embeddings_r2_key and embeddings_r2_key != 'inline' and '/' in embeddings_r2_key:
                    valid_keys.add(embeddings_r2_key)

        logger.info(f"Found {len(valid_keys)} valid R2 keys in database")
        return valid_keys

    finally:
        db.close()


def get_all_r2_files() -> List[str]:
    """
    Get all files stored on R2

    Returns:
        List of R2 keys
    """
    logger.info(f"Listing all files in R2 bucket: {R2_BUCKET_NAME}")
    all_files = list_r2_files()
    logger.info(f"Found {len(all_files)} files on R2")
    return all_files


def find_orphaned_files(valid_keys: Set[str], all_files: List[str]) -> List[str]:
    """
    Find files on R2 that don't have database records

    Args:
        valid_keys: Set of R2 keys that should exist (from database)
        all_files: List of all R2 keys (from R2 storage)

    Returns:
        List of orphaned R2 keys
    """
    orphaned = []

    for r2_key in all_files:
        if r2_key not in valid_keys:
            orphaned.append(r2_key)

    logger.info(f"Found {len(orphaned)} orphaned files")
    return orphaned


def calculate_storage_freed(orphaned_files: List[str]) -> float:
    """
    Estimate storage freed (simplified - actual size would require additional R2 API calls)

    Args:
        orphaned_files: List of orphaned R2 keys

    Returns:
        Estimated storage freed in MB
    """
    # Rough estimate based on file types
    total_mb = 0.0

    for key in orphaned_files:
        if key.endswith('.pdf'):
            total_mb += 2.0  # Assume avg 2MB PDF
        elif key.endswith('_metadata.json'):
            total_mb += 18.0  # Avg 18MB metadata with embeddings
        elif key.endswith('.mp4'):
            total_mb += 1.0  # Avg 1MB video
        else:
            total_mb += 0.5  # Other files

    return total_mb


def main():
    parser = argparse.ArgumentParser(description='Cleanup orphaned R2 files')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what will be deleted without actually deleting'
    )
    args = parser.parse_args()

    # Check R2 credentials
    if not os.getenv('R2_ENDPOINT_URL'):
        logger.error("❌ R2_ENDPOINT_URL not configured")
        sys.exit(1)

    logger.info("=" * 70)
    logger.info("Cleanup Orphaned R2 Files")
    logger.info("=" * 70)

    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No files will be deleted")
    else:
        logger.warning("⚠️  LIVE MODE - Files will be permanently deleted!")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Aborted")
            sys.exit(0)

    # Step 1: Get valid R2 keys from database
    logger.info("\nStep 1: Getting valid R2 keys from database...")
    valid_keys = get_valid_r2_keys_from_db()

    # Step 2: Get all files from R2
    logger.info("\nStep 2: Listing all files on R2...")
    all_files = get_all_r2_files()

    if not all_files:
        logger.warning("No files found on R2")
        sys.exit(0)

    # Step 3: Find orphaned files
    logger.info("\nStep 3: Identifying orphaned files...")
    orphaned_files = find_orphaned_files(valid_keys, all_files)

    if not orphaned_files:
        logger.info("✅ No orphaned files found!")
        sys.exit(0)

    # Step 4: Calculate storage to be freed
    estimated_mb = calculate_storage_freed(orphaned_files)
    logger.info(f"\nEstimated storage to free: ~{estimated_mb:.1f} MB")

    # Step 5: Display orphaned files
    logger.info(f"\nOrphaned files ({len(orphaned_files)}):")
    for i, key in enumerate(orphaned_files, 1):
        logger.info(f"  {i}. {key}")

    # Step 6: Delete (or dry-run)
    if args.dry_run:
        logger.info(f"\n🔍 DRY RUN: Would delete {len(orphaned_files)} files (~{estimated_mb:.1f} MB)")
        logger.info("Run without --dry-run to actually delete these files")
    else:
        logger.info(f"\nDeleting {len(orphaned_files)} orphaned files...")
        deleted_count = 0
        failed_count = 0

        for key in orphaned_files:
            try:
                success = delete_file(key)
                if success:
                    logger.info(f"✅ Deleted: {key}")
                    deleted_count += 1
                else:
                    logger.warning(f"⚠️  Failed to delete: {key}")
                    failed_count += 1
            except Exception as e:
                logger.error(f"❌ Error deleting {key}: {e}")
                failed_count += 1

        logger.info("\n" + "=" * 70)
        logger.info(f"✅ Cleanup complete!")
        logger.info(f"   Deleted: {deleted_count} files")
        logger.info(f"   Failed: {failed_count} files")
        logger.info(f"   Storage freed: ~{estimated_mb:.1f} MB")
        logger.info("=" * 70)


if __name__ == '__main__':
    main()
