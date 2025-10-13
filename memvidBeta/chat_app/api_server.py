"""
REST API Server for Socrate AI
Exposes all Telegram bot functionality via REST endpoints
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pathlib import Path
import sys
import logging
import os
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.config import user_settings_manager
from core.content_generators import (
    generate_quiz_prompt,
    generate_outline_prompt,
    generate_mindmap_prompt,
    generate_summary_prompt,
    generate_analysis_prompt
)
from core.rag_pipeline_robust import process_query_robust as process_query
from utils.file_formatter import (
    format_as_txt,
    format_as_html,
    save_temp_file,
    cleanup_old_exports
)
from database.operations import (
    get_all_documents,
    get_document_by_id,
    add_document,
    delete_document
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# API Key authentication (simple bearer token)
API_KEYS = set(os.getenv("API_KEYS", "").split(","))

def require_api_key(f):
    """Decorator to require API key for protected endpoints"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid authorization header"}), 401

        token = auth_header.split(' ')[1]
        if token not in API_KEYS:
            return jsonify({"error": "Invalid API key"}), 401

        return f(*args, **kwargs)

    return decorated_function


# ============================================================================
# DOCUMENT MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/documents', methods=['GET'])
@require_api_key
def list_documents():
    """
    GET /api/documents
    Returns list of all available documents
    """
    try:
        documents = get_all_documents()
        result = [
            {
                "id": doc.id,
                "filename": doc.filename,
                "doc_type": doc.doc_type,
                "status": doc.status,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None
            }
            for doc in documents
        ]
        return jsonify({"documents": result}), 200
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/documents/<document_id>', methods=['GET'])
@require_api_key
def get_document(document_id: str):
    """
    GET /api/documents/{document_id}
    Returns details of a specific document
    """
    try:
        doc = get_document_by_id(document_id)
        if not doc:
            return jsonify({"error": "Document not found"}), 404

        return jsonify({
            "id": doc.id,
            "filename": doc.filename,
            "doc_type": doc.doc_type,
            "status": doc.status,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None
        }), 200
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# CONTENT GENERATION ENDPOINTS
# ============================================================================

@app.route('/api/quiz', methods=['POST'])
@require_api_key
def generate_quiz():
    """
    POST /api/quiz
    Generate a quiz from document content

    Request body:
    {
        "document_id": "string",
        "topic": "string (optional)",
        "num_questions": int (default: 10),
        "quiz_type": "multiple_choice|true_false|mixed" (default: "multiple_choice"),
        "format": "text|html" (default: "text")
    }
    """
    try:
        data = request.json
        document_id = data.get('document_id')
        topic = data.get('topic', '')
        num_questions = data.get('num_questions', 10)
        quiz_type = data.get('quiz_type', 'multiple_choice')
        output_format = data.get('format', 'text')

        if not document_id:
            return jsonify({"error": "document_id is required"}), 400

        # Verify document exists
        doc = get_document_by_id(document_id)
        if not doc:
            return jsonify({"error": "Document not found"}), 404

        # Generate quiz prompt
        prompt = generate_quiz_prompt(
            topic=topic,
            num_questions=num_questions,
            quiz_type=quiz_type,
            scope='entire'
        )

        # Process query
        result = process_query(
            query=prompt,
            document_id=document_id,
            user_id=None  # API mode - no specific user
        )

        if not result.get('success'):
            return jsonify({"error": "Failed to generate quiz"}), 500

        content = result.get('answer', '')

        # Format output
        if output_format == 'html':
            formatted = format_as_html(
                content=content,
                title=f"Quiz: {topic or doc.filename}",
                content_type="quiz"
            )
        else:
            formatted = format_as_txt(
                content=content,
                title=f"Quiz: {topic or doc.filename}",
                content_type="quiz"
            )

        return jsonify({
            "success": True,
            "content": formatted,
            "format": output_format
        }), 200

    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/summary', methods=['POST'])
@require_api_key
def generate_summary():
    """
    POST /api/summary
    Generate a summary of document content

    Request body:
    {
        "document_id": "string",
        "topic": "string (optional)",
        "scope": "entire|topic" (default: "entire"),
        "format": "text|html" (default: "text")
    }
    """
    try:
        data = request.json
        document_id = data.get('document_id')
        topic = data.get('topic', '')
        scope = data.get('scope', 'entire')
        output_format = data.get('format', 'text')

        if not document_id:
            return jsonify({"error": "document_id is required"}), 400

        doc = get_document_by_id(document_id)
        if not doc:
            return jsonify({"error": "Document not found"}), 404

        # Generate summary prompt
        prompt = generate_summary_prompt(topic=topic, scope=scope)

        # Process query
        result = process_query(
            query=prompt,
            document_id=document_id,
            user_id=None
        )

        if not result.get('success'):
            return jsonify({"error": "Failed to generate summary"}), 500

        content = result.get('answer', '')

        # Format output
        if output_format == 'html':
            formatted = format_as_html(
                content=content,
                title=f"Summary: {topic or doc.filename}",
                content_type="summary"
            )
        else:
            formatted = format_as_txt(
                content=content,
                title=f"Summary: {topic or doc.filename}",
                content_type="summary"
            )

        return jsonify({
            "success": True,
            "content": formatted,
            "format": output_format
        }), 200

    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/mindmap', methods=['POST'])
@require_api_key
def generate_mindmap():
    """
    POST /api/mindmap
    Generate a mindmap of document content

    Request body:
    {
        "document_id": "string",
        "topic": "string (optional)",
        "depth": int (default: 3),
        "format": "text|html" (default: "text")
    }
    """
    try:
        data = request.json
        document_id = data.get('document_id')
        topic = data.get('topic', '')
        depth = data.get('depth', 3)
        output_format = data.get('format', 'text')

        if not document_id:
            return jsonify({"error": "document_id is required"}), 400

        doc = get_document_by_id(document_id)
        if not doc:
            return jsonify({"error": "Document not found"}), 404

        # Generate mindmap prompt
        prompt = generate_mindmap_prompt(topic=topic, depth=depth)

        # Process query
        result = process_query(
            query=prompt,
            document_id=document_id,
            user_id=None
        )

        if not result.get('success'):
            return jsonify({"error": "Failed to generate mindmap"}), 500

        content = result.get('answer', '')

        # Format output
        if output_format == 'html':
            formatted = format_as_html(
                content=content,
                title=f"Mindmap: {topic or doc.filename}",
                content_type="mindmap"
            )
        else:
            formatted = format_as_txt(
                content=content,
                title=f"Mindmap: {topic or doc.filename}",
                content_type="mindmap"
            )

        return jsonify({
            "success": True,
            "content": formatted,
            "format": output_format
        }), 200

    except Exception as e:
        logger.error(f"Error generating mindmap: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/outline', methods=['POST'])
@require_api_key
def generate_outline():
    """
    POST /api/outline
    Generate an outline of document content

    Request body:
    {
        "document_id": "string",
        "topic": "string (optional)",
        "outline_type": "bullets|numbered|hierarchical" (default: "hierarchical"),
        "scope": "entire|topic" (default: "entire"),
        "format": "text|html" (default: "text")
    }
    """
    try:
        data = request.json
        document_id = data.get('document_id')
        topic = data.get('topic', '')
        outline_type = data.get('outline_type', 'hierarchical')
        scope = data.get('scope', 'entire')
        output_format = data.get('format', 'text')

        if not document_id:
            return jsonify({"error": "document_id is required"}), 400

        doc = get_document_by_id(document_id)
        if not doc:
            return jsonify({"error": "Document not found"}), 404

        # Generate outline prompt
        prompt = generate_outline_prompt(
            topic=topic,
            outline_type=outline_type,
            scope=scope
        )

        # Process query
        result = process_query(
            query=prompt,
            document_id=document_id,
            user_id=None
        )

        if not result.get('success'):
            return jsonify({"error": "Failed to generate outline"}), 500

        content = result.get('answer', '')

        # Format output
        if output_format == 'html':
            formatted = format_as_html(
                content=content,
                title=f"Outline: {topic or doc.filename}",
                content_type="outline"
            )
        else:
            formatted = format_as_txt(
                content=content,
                title=f"Outline: {topic or doc.filename}",
                content_type="outline"
            )

        return jsonify({
            "success": True,
            "content": formatted,
            "format": output_format
        }), 200

    except Exception as e:
        logger.error(f"Error generating outline: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
@require_api_key
def analyze_content():
    """
    POST /api/analyze
    Analyze document content with specific analysis type

    Request body:
    {
        "document_id": "string",
        "analysis_type": "themes|arguments|comparisons|critical|structured" (default: "themes"),
        "format": "text|html" (default: "text")
    }
    """
    try:
        data = request.json
        document_id = data.get('document_id')
        analysis_type = data.get('analysis_type', 'themes')
        output_format = data.get('format', 'text')

        if not document_id:
            return jsonify({"error": "document_id is required"}), 400

        doc = get_document_by_id(document_id)
        if not doc:
            return jsonify({"error": "Document not found"}), 404

        # Generate analysis prompt
        prompt = generate_analysis_prompt(analysis_type=analysis_type)

        # Process query
        result = process_query(
            query=prompt,
            document_id=document_id,
            user_id=None
        )

        if not result.get('success'):
            return jsonify({"error": "Failed to analyze content"}), 500

        content = result.get('answer', '')

        # Format output
        if output_format == 'html':
            formatted = format_as_html(
                content=content,
                title=f"Analysis: {doc.filename}",
                content_type="analysis"
            )
        else:
            formatted = format_as_txt(
                content=content,
                title=f"Analysis: {doc.filename}",
                content_type="analysis"
            )

        return jsonify({
            "success": True,
            "content": formatted,
            "format": output_format,
            "analysis_type": analysis_type
        }), 200

    except Exception as e:
        logger.error(f"Error analyzing content: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/query', methods=['POST'])
@require_api_key
def custom_query():
    """
    POST /api/query
    Send a custom query to a document

    Request body:
    {
        "document_id": "string",
        "query": "string",
        "format": "text|html" (default: "text")
    }
    """
    try:
        data = request.json
        document_id = data.get('document_id')
        query = data.get('query')
        output_format = data.get('format', 'text')

        if not document_id or not query:
            return jsonify({"error": "document_id and query are required"}), 400

        doc = get_document_by_id(document_id)
        if not doc:
            return jsonify({"error": "Document not found"}), 404

        # Process query
        result = process_query(
            query=query,
            document_id=document_id,
            user_id=None
        )

        if not result.get('success'):
            return jsonify({"error": "Failed to process query"}), 500

        content = result.get('answer', '')

        # Format output
        if output_format == 'html':
            formatted = format_as_html(
                content=content,
                title=f"Query: {doc.filename}",
                content_type="query"
            )
        else:
            formatted = format_as_txt(
                content=content,
                title=f"Query: {doc.filename}",
                content_type="query"
            )

        return jsonify({
            "success": True,
            "content": formatted,
            "format": output_format
        }), 200

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Socrate AI API"
    }), 200


if __name__ == '__main__':
    # Get port from environment or default to 5000
    port = int(os.getenv('PORT', 5000))

    logger.info(f"Starting Socrate AI API server on port {port}")

    # Run server
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )
