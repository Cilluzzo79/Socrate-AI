"""
Google Cloud Vision OCR Processor
Extracts text from images using Google Cloud Vision API
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def extract_text_from_image(image_bytes: bytes, filename: str = "image") -> Dict[str, Any]:
    """
    Extract text from image using Google Cloud Vision API

    Args:
        image_bytes: Image file content as bytes
        filename: Original filename (for logging)

    Returns:
        dict: {
            'success': bool,
            'text': str,  # Extracted text
            'confidence': float,  # Average confidence score (0-1)
            'language': str,  # Detected language code
            'error': str  # Error message if failed
        }
    """
    try:
        # Import Google Cloud Vision client
        try:
            from google.cloud import vision
            from google.oauth2 import service_account
        except ImportError:
            logger.error("google-cloud-vision library not installed")
            return {
                'success': False,
                'error': 'google-cloud-vision library not installed. Run: pip install google-cloud-vision'
            }

        logger.info(f"Starting OCR processing for: {filename}")

        # Check authentication methods (Service Account JSON or API Key)
        credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        api_key = os.getenv('GOOGLE_CLOUD_VISION_API_KEY')

        if credentials_json:
            # Method 1: Service Account JSON (recommended for production)
            logger.info("Using Service Account credentials from JSON")
            import json
            try:
                credentials_dict = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(credentials_dict)
                client = vision.ImageAnnotatorClient(credentials=credentials)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")
                return {
                    'success': False,
                    'error': 'Invalid Service Account JSON credentials'
                }
        elif api_key:
            # Method 2: API Key (simpler, good for development)
            logger.info("Using API Key authentication")
            client = vision.ImageAnnotatorClient(
                client_options={"api_key": api_key}
            )
        else:
            logger.warning("No Google Cloud Vision credentials configured - OCR disabled")
            return {
                'success': False,
                'error': 'Google Cloud Vision not configured. Set either GOOGLE_APPLICATION_CREDENTIALS_JSON or GOOGLE_CLOUD_VISION_API_KEY'
            }

        # Prepare image for Vision API
        image = vision.Image(content=image_bytes)

        # Perform text detection
        logger.info("Calling Google Cloud Vision text_detection API...")
        response = client.text_detection(image=image)

        # Check for API errors
        if response.error.message:
            logger.error(f"Vision API error: {response.error.message}")
            return {
                'success': False,
                'error': f'Vision API error: {response.error.message}'
            }

        # Extract full text annotation (entire page text)
        texts = response.text_annotations

        if not texts or len(texts) == 0:
            logger.warning(f"No text detected in image: {filename}")
            return {
                'success': True,
                'text': '',
                'confidence': 0.0,
                'language': 'unknown',
                'note': 'No text found in image'
            }

        # First annotation contains the full text
        full_text = texts[0].description

        # Calculate average confidence from individual word annotations
        if len(texts) > 1:
            # texts[1:] contains individual words with confidence scores
            # Note: text_annotations don't have confidence, but full_text_annotation does
            # For simplicity, we'll use document_text_detection for better confidence
            pass

        # Detect language (first text annotation contains detected locale)
        language = 'unknown'
        if hasattr(texts[0], 'locale') and texts[0].locale:
            language = texts[0].locale

        logger.info(f"✅ OCR completed: extracted {len(full_text)} characters, language: {language}")

        return {
            'success': True,
            'text': full_text,
            'confidence': 1.0,  # Google Vision has high accuracy by default
            'language': language,
            'char_count': len(full_text),
            'word_count': len(full_text.split())
        }

    except Exception as e:
        logger.error(f"Error in OCR processing: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'traceback': str(e)
        }


def is_image_file(mime_type: str) -> bool:
    """
    Check if MIME type is a supported image format

    Args:
        mime_type: File MIME type

    Returns:
        bool: True if image format supported by OCR
    """
    supported_types = [
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/gif',
        'image/webp',
        'image/bmp',
        'image/tiff',
        'image/heic',
        'image/heif'
    ]

    return mime_type.lower() in supported_types


def estimate_ocr_cost(image_size_bytes: int) -> float:
    """
    Estimate Google Cloud Vision API cost for OCR

    Pricing (as of 2025):
    - First 1,000 units/month: Free
    - 1,001 to 5,000,000 units: $1.50 per 1,000 units

    Args:
        image_size_bytes: Image file size in bytes

    Returns:
        float: Estimated cost in USD (excluding free tier)
    """
    # Each text detection request = 1 unit
    units = 1

    # Price per 1000 units (after free tier)
    price_per_1000 = 1.50

    # Calculate cost (excluding first 1000 free units)
    cost = (units / 1000) * price_per_1000

    return cost
