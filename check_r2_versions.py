"""
Check and cleanup R2 object versions
Useful when versioning is enabled and old versions consume storage
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from core.s3_storage import get_s3_client, R2_BUCKET_NAME
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def list_all_versions():
    """
    List all object versions (current + old)
    """
    try:
        client = get_s3_client()

        logger.info(f"Listing all versions in bucket: {R2_BUCKET_NAME}")

        # List object versions
        paginator = client.get_paginator('list_object_versions')

        current_objects = []
        old_versions = []
        delete_markers = []

        total_size = 0

        for page in paginator.paginate(Bucket=R2_BUCKET_NAME):
            # Current versions
            if 'Versions' in page:
                for version in page['Versions']:
                    size_mb = version['Size'] / (1024 * 1024)
                    total_size += version['Size']

                    obj_info = {
                        'key': version['Key'],
                        'version_id': version['VersionId'],
                        'is_latest': version['IsLatest'],
                        'size': version['Size'],
                        'size_mb': round(size_mb, 2),
                        'last_modified': version['LastModified']
                    }

                    if version['IsLatest']:
                        current_objects.append(obj_info)
                    else:
                        old_versions.append(obj_info)

            # Delete markers
            if 'DeleteMarkers' in page:
                for marker in page['DeleteMarkers']:
                    delete_markers.append({
                        'key': marker['Key'],
                        'version_id': marker['VersionId'],
                        'is_latest': marker['IsLatest'],
                        'last_modified': marker['LastModified']
                    })

        # Summary
        total_size_mb = total_size / (1024 * 1024)

        logger.info("=" * 70)
        logger.info("SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Current objects: {len(current_objects)}")
        logger.info(f"Old versions: {len(old_versions)}")
        logger.info(f"Delete markers: {len(delete_markers)}")
        logger.info(f"Total storage used: {total_size_mb:.2f} MB")
        logger.info("")

        # Current objects detail
        if current_objects:
            logger.info("Current objects:")
            current_size = 0
            for obj in current_objects:
                logger.info(f"  - {obj['key']}: {obj['size_mb']} MB")
                current_size += obj['size']
            logger.info(f"  SUBTOTAL: {current_size / (1024 * 1024):.2f} MB")
            logger.info("")

        # Old versions detail
        if old_versions:
            logger.info(f"Old versions ({len(old_versions)} objects):")
            old_size = 0
            for obj in old_versions[:20]:  # Show first 20
                logger.info(f"  - {obj['key']} (version: {obj['version_id'][:8]}...): {obj['size_mb']} MB")
                old_size += obj['size']

            if len(old_versions) > 20:
                logger.info(f"  ... and {len(old_versions) - 20} more")

            logger.info(f"  SUBTOTAL: {old_size / (1024 * 1024):.2f} MB")
            logger.info("")

        # Delete markers
        if delete_markers:
            logger.info(f"Delete markers: {len(delete_markers)}")
            for marker in delete_markers[:10]:
                logger.info(f"  - {marker['key']}")
            logger.info("")

        return {
            'current_objects': current_objects,
            'old_versions': old_versions,
            'delete_markers': delete_markers,
            'total_size_mb': total_size_mb
        }

    except Exception as e:
        logger.error(f"Error listing versions: {e}")
        import traceback
        traceback.print_exc()
        return None


def cleanup_old_versions(dry_run=True):
    """
    Delete old versions and delete markers
    """
    try:
        client = get_s3_client()

        # First, list all versions
        data = list_all_versions()
        if not data:
            return

        old_versions = data['old_versions']
        delete_markers = data['delete_markers']

        if not old_versions and not delete_markers:
            logger.info("✅ No old versions or delete markers to clean!")
            return

        total_to_delete = len(old_versions) + len(delete_markers)

        if dry_run:
            logger.info("=" * 70)
            logger.info(f"DRY RUN: Would delete {total_to_delete} items")
            logger.info(f"  - Old versions: {len(old_versions)}")
            logger.info(f"  - Delete markers: {len(delete_markers)}")
            logger.info("=" * 70)
            logger.info("Run with --live to actually delete")
            return

        logger.info("=" * 70)
        logger.info(f"DELETING {total_to_delete} items...")
        logger.info("=" * 70)

        deleted_count = 0
        failed_count = 0
        freed_size = 0

        # Delete old versions
        for obj in old_versions:
            try:
                client.delete_object(
                    Bucket=R2_BUCKET_NAME,
                    Key=obj['key'],
                    VersionId=obj['version_id']
                )
                logger.info(f"✅ Deleted old version: {obj['key']} ({obj['size_mb']} MB)")
                deleted_count += 1
                freed_size += obj['size']
            except Exception as e:
                logger.error(f"❌ Failed to delete {obj['key']}: {e}")
                failed_count += 1

        # Delete markers
        for marker in delete_markers:
            try:
                client.delete_object(
                    Bucket=R2_BUCKET_NAME,
                    Key=marker['key'],
                    VersionId=marker['version_id']
                )
                logger.info(f"✅ Deleted delete marker: {marker['key']}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to delete marker {marker['key']}: {e}")
                failed_count += 1

        freed_mb = freed_size / (1024 * 1024)

        logger.info("=" * 70)
        logger.info("CLEANUP COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Deleted: {deleted_count} items")
        logger.info(f"Failed: {failed_count} items")
        logger.info(f"Storage freed: {freed_mb:.2f} MB")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Check and cleanup R2 versions')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup old versions')
    parser.add_argument('--live', action='store_true', help='Actually delete (not dry-run)')

    args = parser.parse_args()

    if args.cleanup:
        cleanup_old_versions(dry_run=not args.live)
    else:
        list_all_versions()
