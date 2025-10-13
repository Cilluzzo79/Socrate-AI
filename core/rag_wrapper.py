"""
RAG Pipeline Wrapper for Multi-tenant System
Adapts memvidBeta RAG pipeline to work with new database schema
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Setup logging
logger = logging.getLogger(__name__)

# Try to import memvidBeta components
try:
    # Add memvidBeta to path
    memvid_beta_path = Path(__file__).parent.parent / 'memvidBeta' / 'chat_app'
    sys.path.insert(0, str(memvid_beta_path))

    from core.rag_pipeline_robust import process_query_robust as memvid_process_query
    from core.content_generators import (
        generate_quiz_prompt,
        generate_summary_prompt,
        generate_mindmap_prompt,
        generate_outline_prompt,
        generate_analysis_prompt
    )

    MEMVID_AVAILABLE = True
    logger.info("✅ memvidBeta RAG pipeline loaded successfully")

except ImportError as e:
    MEMVID_AVAILABLE = False
    logger.warning(f"⚠️ memvidBeta RAG pipeline not available: {e}")
    logger.warning("Will use placeholder responses")


def process_query_multitenant(
    user_id: str,
    document_id: str,
    query: str,
    command_type: str = 'query',
    **kwargs
) -> Dict[str, Any]:
    """
    Process a query using memvidBeta RAG pipeline
    Adapted for multi-tenant system

    Args:
        user_id: User UUID (from new database)
        document_id: Document UUID (from new database)
        query: User's query
        command_type: Type of command (quiz, summary, etc.)
        **kwargs: Additional parameters

    Returns:
        Dict with answer, sources, and metadata
    """

    if not MEMVID_AVAILABLE:
        # Placeholder response when memvidBeta not available
        return {
            'success': False,
            'answer': f"[Sistema in configurazione] La funzionalità RAG non è ancora disponibile. Query ricevuta: {query}",
            'sources': [],
            'metadata': {
                'error': 'memvid_not_available'
            }
        }

    try:
        # Get user info from database
        from core.database import get_user_by_id, SessionLocal
        from core.document_operations import get_document_by_id

        user = get_user_by_id(user_id)
        if not user:
            return {
                'success': False,
                'answer': 'Utente non trovato',
                'sources': [],
                'metadata': {'error': 'user_not_found'}
            }

        doc = get_document_by_id(document_id, user_id)
        if not doc:
            return {
                'success': False,
                'answer': 'Documento non trovato o non accessibile',
                'sources': [],
                'metadata': {'error': 'document_not_found'}
            }

        # TODO: Map new document to memvidBeta document format
        # For now, use placeholder document_id
        # In production, you need to:
        # 1. Process uploaded documents with memvid encoder
        # 2. Store memvid index file paths in document metadata
        # 3. Pass those paths to the RAG pipeline

        # Call memvidBeta RAG pipeline
        # Note: This needs adaptation based on how documents are processed
        logger.info(f"Processing query for user {user.telegram_id}, document {doc.filename}")

        response_text, metadata = memvid_process_query(
            user_id=user.telegram_id,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            user_username=user.username,
            query=query,
            document_id=str(doc.id),  # This needs to be mapped to memvid document
            include_history=True
        )

        return {
            'success': True,
            'answer': response_text,
            'sources': metadata.get('sources', []),
            'metadata': metadata
        }

    except Exception as e:
        logger.error(f"Error in RAG pipeline: {e}", exc_info=True)
        return {
            'success': False,
            'answer': f"Errore nell'elaborazione della query: {str(e)}",
            'sources': [],
            'metadata': {
                'error': str(e)
            }
        }


def generate_content(
    user_id: str,
    document_id: str,
    content_type: str,
    **params
) -> Dict[str, Any]:
    """
    Generate structured content (quiz, summary, etc.)

    Args:
        user_id: User UUID
        document_id: Document UUID
        content_type: Type of content (quiz, summary, mindmap, outline, analysis)
        **params: Parameters for content generation

    Returns:
        Dict with generated content
    """

    # Generate appropriate prompt based on content type
    if content_type == 'quiz':
        prompt = generate_quiz_prompt(
            quiz_type=params.get('quiz_type', 'multiple_choice'),
            num_questions=params.get('num_questions', 10),
            difficulty=params.get('difficulty', 'medium'),
            focus_area=params.get('focus_area')
        )

    elif content_type == 'summary':
        prompt = generate_summary_prompt(
            summary_type=params.get('summary_type', 'medium'),
            length=params.get('length', '3-5 paragrafi'),
            focus_area=params.get('focus_area')
        )

    elif content_type == 'mindmap':
        prompt = generate_mindmap_prompt(
            central_concept=params.get('central_concept'),
            depth_level=params.get('depth_level', 3),
            focus_area=params.get('focus_area')
        )

    elif content_type == 'outline':
        prompt = generate_outline_prompt(
            outline_type=params.get('outline_type', 'hierarchical'),
            detail_level=params.get('detail_level', 'medium'),
            focus_area=params.get('focus_area')
        )

    elif content_type == 'analyze':
        prompt = generate_analysis_prompt(
            analysis_type=params.get('analysis_type', 'thematic'),
            focus_area=params.get('focus_area'),
            depth=params.get('depth', 'profonda')
        )

    else:
        return {
            'success': False,
            'answer': f'Tipo di contenuto non supportato: {content_type}',
            'metadata': {'error': 'unsupported_content_type'}
        }

    # Process the query with the generated prompt
    return process_query_multitenant(
        user_id=user_id,
        document_id=document_id,
        query=prompt,
        command_type=content_type,
        **params
    )


# Export functions
__all__ = [
    'process_query_multitenant',
    'generate_content',
    'MEMVID_AVAILABLE'
]
