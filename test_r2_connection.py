"""
Test R2 Connection and Configuration
Quick diagnostic script to verify R2 credentials and connectivity
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_r2_configuration():
    """Test R2 environment variables and connection"""

    print("=" * 60)
    print("R2 CONFIGURATION TEST")
    print("=" * 60)

    # 1. Check environment variables
    print("\n1. Checking Environment Variables:")
    print("-" * 60)

    r2_access_key = os.getenv('R2_ACCESS_KEY_ID')
    r2_secret_key = os.getenv('R2_SECRET_ACCESS_KEY')
    r2_endpoint = os.getenv('R2_ENDPOINT_URL')
    r2_bucket = os.getenv('R2_BUCKET_NAME', 'socrate-ai-storage')

    print(f"R2_ACCESS_KEY_ID: {'✅ SET' if r2_access_key else '❌ MISSING'}")
    if r2_access_key:
        print(f"  Value: {r2_access_key[:10]}...{r2_access_key[-4:]}")

    print(f"R2_SECRET_ACCESS_KEY: {'✅ SET' if r2_secret_key else '❌ MISSING'}")
    if r2_secret_key:
        print(f"  Value: {r2_secret_key[:10]}...{r2_secret_key[-4:]}")

    print(f"R2_ENDPOINT_URL: {'✅ SET' if r2_endpoint else '❌ MISSING'}")
    if r2_endpoint:
        print(f"  Value: {r2_endpoint}")

    print(f"R2_BUCKET_NAME: {r2_bucket}")

    if not all([r2_access_key, r2_secret_key, r2_endpoint]):
        print("\n❌ ERROR: Missing required R2 credentials")
        print("\nRequired environment variables:")
        print("  - R2_ACCESS_KEY_ID")
        print("  - R2_SECRET_ACCESS_KEY")
        print("  - R2_ENDPOINT_URL")
        print("  - R2_BUCKET_NAME (optional, defaults to 'socrate-ai-storage')")
        return False

    # 2. Test boto3 import
    print("\n2. Checking boto3 installation:")
    print("-" * 60)

    try:
        import boto3
        from botocore.client import Config
        from botocore.exceptions import ClientError
        print("✅ boto3 installed successfully")
        print(f"   Version: {boto3.__version__}")
    except ImportError as e:
        print(f"❌ boto3 not installed: {e}")
        print("\nInstall with: pip install boto3")
        return False

    # 3. Create S3 client
    print("\n3. Creating S3 client:")
    print("-" * 60)

    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=r2_endpoint,
            aws_access_key_id=r2_access_key,
            aws_secret_access_key=r2_secret_key,
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )
        print("✅ S3 client created successfully")
    except Exception as e:
        print(f"❌ Failed to create S3 client: {e}")
        return False

    # 4. Test bucket access (list objects)
    print("\n4. Testing bucket access:")
    print("-" * 60)

    try:
        response = s3_client.list_objects_v2(
            Bucket=r2_bucket,
            MaxKeys=5
        )

        print(f"✅ Successfully connected to bucket: {r2_bucket}")

        if 'Contents' in response:
            print(f"   Found {len(response['Contents'])} objects (showing first 5)")
            for obj in response['Contents']:
                print(f"   - {obj['Key']} ({obj['Size']} bytes)")
        else:
            print("   Bucket is empty (no objects found)")

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ Bucket access failed: {error_code}")
        print(f"   Message: {error_message}")

        if error_code == 'NoSuchBucket':
            print(f"\n   Bucket '{r2_bucket}' does not exist")
            print("   Create it in Cloudflare R2 dashboard")
        elif error_code == 'InvalidAccessKeyId':
            print("\n   Access Key ID is invalid")
            print("   Verify R2_ACCESS_KEY_ID in environment variables")
        elif error_code == 'SignatureDoesNotMatch':
            print("\n   Secret Access Key is invalid")
            print("   Verify R2_SECRET_ACCESS_KEY in environment variables")

        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    # 5. Test upload (small test file)
    print("\n5. Testing file upload:")
    print("-" * 60)

    test_data = b"Test file from Socrate AI - R2 connection test"
    test_key = "test/connection_test.txt"

    try:
        s3_client.put_object(
            Bucket=r2_bucket,
            Key=test_key,
            Body=test_data,
            ContentType='text/plain'
        )
        print(f"✅ Successfully uploaded test file: {test_key}")
        print(f"   Size: {len(test_data)} bytes")

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ Upload failed: {error_code}")
        print(f"   Message: {error_message}")
        return False
    except Exception as e:
        print(f"❌ Unexpected upload error: {e}")
        return False

    # 6. Test download
    print("\n6. Testing file download:")
    print("-" * 60)

    try:
        response = s3_client.get_object(
            Bucket=r2_bucket,
            Key=test_key
        )

        downloaded_data = response['Body'].read()
        print(f"✅ Successfully downloaded test file")
        print(f"   Size: {len(downloaded_data)} bytes")

        if downloaded_data == test_data:
            print("✅ Downloaded data matches uploaded data")
        else:
            print("❌ Data mismatch!")

    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

    # 7. Test delete
    print("\n7. Cleaning up test file:")
    print("-" * 60)

    try:
        s3_client.delete_object(
            Bucket=r2_bucket,
            Key=test_key
        )
        print(f"✅ Successfully deleted test file")

    except Exception as e:
        print(f"❌ Delete failed: {e}")
        print("   (File may still exist in bucket)")

    # 8. Test with core.s3_storage module
    print("\n8. Testing core.s3_storage module:")
    print("-" * 60)

    try:
        from core.s3_storage import upload_file, download_file, delete_file, generate_file_key

        print("✅ Module imported successfully")

        # Test file key generation
        test_user_id = "test-user-123"
        test_doc_id = "test-doc-456"
        test_filename = "test document.pdf"

        file_key = generate_file_key(test_user_id, test_doc_id, test_filename)
        print(f"   Generated key: {file_key}")

        # Test upload via module
        test_data_2 = b"Module test data"
        upload_success = upload_file(test_data_2, file_key, 'application/pdf')

        if upload_success:
            print(f"✅ Module upload successful")

            # Test download via module
            downloaded = download_file(file_key)
            if downloaded == test_data_2:
                print(f"✅ Module download successful")
            else:
                print(f"❌ Module download data mismatch")

            # Cleanup
            delete_file(file_key)
            print(f"✅ Module cleanup successful")
        else:
            print(f"❌ Module upload failed")
            return False

    except Exception as e:
        print(f"❌ Module test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Success!
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nR2 configuration is correct and working.")
    print("You can now upload documents via the API.")

    return True


if __name__ == '__main__':
    try:
        success = test_r2_configuration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
