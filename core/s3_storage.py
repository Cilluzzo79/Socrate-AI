"""
S3-Compatible Storage Helper for Cloudflare R2
Handles file upload/download to cloud storage
"""

import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import logging
from typing import Optional, BinaryIO

logger = logging.getLogger(__name__)

# R2 Configuration from environment
R2_ACCESS_KEY = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_ENDPOINT = os.getenv('R2_ENDPOINT_URL')
R2_BUCKET = os.getenv('R2_BUCKET_NAME', 'socrate-ai-storage')

# Initialize S3 client for R2
s3_client = None

def get_s3_client():
    """Get or create S3 client for R2"""
    global s3_client

    if s3_client is None:
        if not all([R2_ACCESS_KEY, R2_SECRET_KEY, R2_ENDPOINT]):
            logger.error("R2 credentials not configured")
            raise ValueError("R2 credentials missing in environment variables")

        s3_client = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name='auto'  # R2 uses 'auto' region
        )
        logger.info(f"S3 client initialized for R2: {R2_ENDPOINT}")

    return s3_client


def upload_file(file_data: bytes, file_key: str, content_type: str = 'application/octet-stream') -> bool:
    """
    Upload file to R2

    Args:
        file_data: Binary file content
        file_key: S3 key (path) for the file, e.g., 'users/user-id/doc-id/file.pdf'
        content_type: MIME type

    Returns:
        bool: True if successful
    """
    try:
        client = get_s3_client()

        client.put_object(
            Bucket=R2_BUCKET,
            Key=file_key,
            Body=file_data,
            ContentType=content_type
        )

        logger.info(f"File uploaded to R2: {file_key} ({len(file_data)} bytes)")
        return True

    except ClientError as e:
        logger.error(f"Error uploading to R2: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error uploading to R2: {e}")
        return False


def download_file(file_key: str) -> Optional[bytes]:
    """
    Download file from R2

    Args:
        file_key: S3 key (path) for the file

    Returns:
        bytes: File content, or None if error
    """
    try:
        client = get_s3_client()

        response = client.get_object(
            Bucket=R2_BUCKET,
            Key=file_key
        )

        file_data = response['Body'].read()
        logger.info(f"File downloaded from R2: {file_key} ({len(file_data)} bytes)")
        return file_data

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.error(f"File not found in R2: {file_key}")
        else:
            logger.error(f"Error downloading from R2: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading from R2: {e}")
        return None


def delete_file(file_key: str) -> bool:
    """
    Delete file from R2

    Args:
        file_key: S3 key (path) for the file

    Returns:
        bool: True if successful
    """
    try:
        client = get_s3_client()

        client.delete_object(
            Bucket=R2_BUCKET,
            Key=file_key
        )

        logger.info(f"File deleted from R2: {file_key}")
        return True

    except ClientError as e:
        logger.error(f"Error deleting from R2: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error deleting from R2: {e}")
        return False


def file_exists(file_key: str) -> bool:
    """
    Check if file exists in R2

    Args:
        file_key: S3 key (path) for the file

    Returns:
        bool: True if file exists
    """
    try:
        client = get_s3_client()

        client.head_object(
            Bucket=R2_BUCKET,
            Key=file_key
        )

        return True

    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        logger.error(f"Error checking file existence: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking file: {e}")
        return False


def generate_file_key(user_id: str, document_id: str, filename: str) -> str:
    """
    Generate S3 key for a file

    Args:
        user_id: User UUID
        document_id: Document UUID
        filename: Original filename

    Returns:
        str: S3 key, e.g., 'users/abc-123/docs/xyz-789/file.pdf'
    """
    # Sanitize filename (remove special characters)
    safe_filename = "".join(c for c in filename if c.isalnum() or c in ('._- ')).strip()

    return f"users/{user_id}/docs/{document_id}/{safe_filename}"
