"""
Multi-tenant Document Operations
All operations require user_id for data isolation
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from core.database import SessionLocal, User, Document, ChatSession


# ============================================================================
# DOCUMENT OPERATIONS
# ============================================================================

def get_user_documents(user_id: str, status: Optional[str] = None) -> List[Document]:
    """
    Get all documents for a specific user

    Args:
        user_id: User UUID
        status: Optional filter by status (ready, processing, failed)

    Returns:
        List of Document objects
    """
    db = SessionLocal()
    try:
        query = db.query(Document).filter_by(user_id=uuid.UUID(user_id))

        if status:
            query = query.filter_by(status=status)

        return query.order_by(Document.created_at.desc()).all()
    finally:
        db.close()


def get_document_by_id(document_id: str, user_id: str) -> Optional[Document]:
    """
    Get document by ID with user ownership verification

    Args:
        document_id: Document UUID
        user_id: User UUID (for ownership check)

    Returns:
        Document object or None if not found/unauthorized
    """
    db = SessionLocal()
    try:
        return db.query(Document).filter_by(
            id=uuid.UUID(document_id),
            user_id=uuid.UUID(user_id)
        ).first()
    finally:
        db.close()


def create_document(
    user_id: str,
    filename: str,
    file_path: str,
    file_size: int,
    mime_type: str = None,
    **kwargs
) -> Document:
    """
    Create new document for user

    Args:
        user_id: User UUID
        filename: Document filename
        file_path: Storage path
        file_size: File size in bytes
        mime_type: MIME type
        **kwargs: Additional fields

    Returns:
        Created Document object
    """
    db = SessionLocal()
    try:
        # Verify user exists
        user = db.query(User).filter_by(id=uuid.UUID(user_id)).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Check storage quota
        file_size_mb = file_size / (1024 * 1024)
        if user.storage_used_mb + file_size_mb > user.storage_quota_mb:
            raise ValueError(f"Storage quota exceeded. Used: {user.storage_used_mb}MB, Quota: {user.storage_quota_mb}MB")

        # Create document
        doc = Document(
            user_id=uuid.UUID(user_id),
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            status='processing',
            processing_started_at=datetime.utcnow(),
            **kwargs
        )
        db.add(doc)

        # Update user storage
        user.storage_used_mb += file_size_mb

        db.commit()
        db.refresh(doc)
        return doc

    finally:
        db.close()


def update_document_status(
    document_id: str,
    user_id: str,
    status: str,
    **kwargs
) -> Optional[Document]:
    """
    Update document status and metadata

    Args:
        document_id: Document UUID
        user_id: User UUID (for ownership check)
        status: New status
        **kwargs: Additional fields to update

    Returns:
        Updated Document or None
    """
    db = SessionLocal()
    try:
        doc = db.query(Document).filter_by(
            id=uuid.UUID(document_id),
            user_id=uuid.UUID(user_id)
        ).first()

        if not doc:
            return None

        doc.status = status
        doc.updated_at = datetime.utcnow()

        if status == 'ready':
            doc.processing_completed_at = datetime.utcnow()
            doc.processing_progress = 100

        for key, value in kwargs.items():
            if hasattr(doc, key):
                setattr(doc, key, value)

        db.commit()
        db.refresh(doc)
        return doc

    finally:
        db.close()


def delete_document(document_id: str, user_id: str) -> bool:
    """
    Delete document and free up user storage

    Args:
        document_id: Document UUID
        user_id: User UUID (for ownership check)

    Returns:
        True if deleted, False otherwise
    """
    db = SessionLocal()
    try:
        doc = db.query(Document).filter_by(
            id=uuid.UUID(document_id),
            user_id=uuid.UUID(user_id)
        ).first()

        if not doc:
            return False

        # Get user to update storage
        user = db.query(User).filter_by(id=uuid.UUID(user_id)).first()
        if user and doc.file_size:
            file_size_mb = doc.file_size / (1024 * 1024)
            user.storage_used_mb = max(0, user.storage_used_mb - file_size_mb)

        db.delete(doc)
        db.commit()
        return True

    finally:
        db.close()


# ============================================================================
# CHAT SESSION OPERATIONS
# ============================================================================

def create_chat_session(
    user_id: str,
    command_type: str,
    request_data: Dict[str, Any],
    channel: str,
    document_id: Optional[str] = None,
    **kwargs
) -> ChatSession:
    """
    Create new chat session

    Args:
        user_id: User UUID
        command_type: Type of command (quiz, summary, etc.)
        request_data: Input parameters
        channel: Channel (telegram, web_app, api)
        document_id: Optional document UUID
        **kwargs: Additional fields

    Returns:
        Created ChatSession object
    """
    db = SessionLocal()
    try:
        session = ChatSession(
            user_id=uuid.UUID(user_id),
            document_id=uuid.UUID(document_id) if document_id else None,
            command_type=command_type,
            request_data=request_data,
            channel=channel,
            **kwargs
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    finally:
        db.close()


def update_chat_session(
    session_id: str,
    response_data: Dict[str, Any],
    **kwargs
) -> Optional[ChatSession]:
    """
    Update chat session with response

    Args:
        session_id: ChatSession UUID
        response_data: Generated output
        **kwargs: Additional fields (tokens_used, generation_time_ms, etc.)

    Returns:
        Updated ChatSession or None
    """
    db = SessionLocal()
    try:
        session = db.query(ChatSession).filter_by(id=uuid.UUID(session_id)).first()

        if not session:
            return None

        session.response_data = response_data

        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)

        db.commit()
        db.refresh(session)
        return session

    finally:
        db.close()


def get_user_chat_history(
    user_id: str,
    limit: int = 50,
    document_id: Optional[str] = None
) -> List[ChatSession]:
    """
    Get user's chat history

    Args:
        user_id: User UUID
        limit: Maximum number of sessions to return
        document_id: Optional filter by document

    Returns:
        List of ChatSession objects
    """
    db = SessionLocal()
    try:
        query = db.query(ChatSession).filter_by(user_id=uuid.UUID(user_id))

        if document_id:
            query = query.filter_by(document_id=uuid.UUID(document_id))

        return query.order_by(ChatSession.created_at.desc()).limit(limit).all()

    finally:
        db.close()


# ============================================================================
# ANALYTICS & STATISTICS
# ============================================================================

def get_user_stats(user_id: str) -> Dict[str, Any]:
    """
    Get user statistics

    Args:
        user_id: User UUID

    Returns:
        Dictionary with stats
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(id=uuid.UUID(user_id)).first()
        if not user:
            return {}

        # Count documents by status
        documents = db.query(Document).filter_by(user_id=uuid.UUID(user_id)).all()
        doc_stats = {
            'total': len(documents),
            'ready': sum(1 for d in documents if d.status == 'ready'),
            'processing': sum(1 for d in documents if d.status == 'processing'),
            'failed': sum(1 for d in documents if d.status == 'failed')
        }

        # Count chat sessions
        total_sessions = db.query(ChatSession).filter_by(user_id=uuid.UUID(user_id)).count()

        # Count by command type
        sessions = db.query(ChatSession).filter_by(user_id=uuid.UUID(user_id)).all()
        command_stats = {}
        for session in sessions:
            cmd = session.command_type
            command_stats[cmd] = command_stats.get(cmd, 0) + 1

        return {
            'user': {
                'telegram_id': user.telegram_id,
                'first_name': user.first_name,
                'subscription_tier': user.subscription_tier,
                'storage_used_mb': user.storage_used_mb,
                'storage_quota_mb': user.storage_quota_mb,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            },
            'documents': doc_stats,
            'chat_sessions': {
                'total': total_sessions,
                'by_command': command_stats
            }
        }

    finally:
        db.close()
