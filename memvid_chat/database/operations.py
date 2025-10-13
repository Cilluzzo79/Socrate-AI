"""
Database operations for the Memvid Chat system.
Provides functions for CRUD operations on database models.
"""

from pathlib import Path
import sys
import datetime
from typing import List, Dict, Any, Optional, Tuple

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from database.models import User, Document, Conversation, Message, get_session
from config.config import get_available_documents


def ensure_user_exists(telegram_id: int, first_name: str, last_name: Optional[str] = None, 
                      username: Optional[str] = None) -> User:
    """
    Ensure a user exists in the database, creating if necessary.
    
    Args:
        telegram_id: The Telegram user ID
        first_name: User's first name
        last_name: User's last name (optional)
        username: User's username (optional)
        
    Returns:
        User: The user object
    """
    session = get_session()
    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        # Create new user
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username
        )
        session.add(user)
        session.commit()
    else:
        # Update user information
        user.last_active = datetime.datetime.utcnow()
        if first_name != user.first_name or last_name != user.last_name or username != user.username:
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            session.commit()
    
    session.close()
    return user


def sync_documents() -> List[Document]:
    """
    Synchronize the documents in the database with the actual files in the output directory.
    
    Returns:
        List[Document]: List of all documents in the database
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Starting document synchronization")
    
    session = get_session()
    
    try:
        # Get all documents from the file system
        available_docs = get_available_documents()
        logger.info(f"Found {len(available_docs)} documents in the filesystem")
        
        # Verify files exist
        valid_docs = []
        for doc in available_docs:
            video_file = Path(doc["video_path"])
            index_file = Path(doc["index_path"])
            
            if not video_file.exists():
                logger.warning(f"Video file not found: {video_file}")
                continue
                
            if not index_file.exists():
                logger.warning(f"Index file not found: {index_file}")
                continue
                
            valid_docs.append(doc)
        
        logger.info(f"{len(valid_docs)} out of {len(available_docs)} documents are valid")
        available_docs = valid_docs
        
        # Get all documents from the database
        db_docs = session.query(Document).all()
        db_doc_ids = {doc.document_id for doc in db_docs}
        logger.info(f"Found {len(db_docs)} documents in the database")
        
        # Add new documents
        added_count = 0
        for doc_info in available_docs:
            if doc_info["id"] not in db_doc_ids:
                doc = Document(
                    document_id=doc_info["id"],
                    name=doc_info["name"],
                    video_path=doc_info["video_path"],
                    index_path=doc_info["index_path"],
                    size_mb=doc_info["size_mb"]
                )
                session.add(doc)
                added_count += 1
                logger.info(f"Added new document: {doc_info['name']} ({doc_info['id']})")
        
        # Update existing documents
        updated_count = 0
        for doc_info in available_docs:
            if doc_info["id"] in db_doc_ids:
                doc = session.query(Document).filter(Document.document_id == doc_info["id"]).first()
                doc.video_path = doc_info["video_path"]
                doc.index_path = doc_info["index_path"]
                doc.size_mb = doc_info["size_mb"]
                updated_count += 1
                logger.info(f"Updated document: {doc_info['name']} ({doc_info['id']})")
        
        # Remove documents that no longer exist
        available_doc_ids = {doc["id"] for doc in available_docs}
        removed_count = 0
        for doc in db_docs:
            if doc.document_id not in available_doc_ids:
                session.delete(doc)
                removed_count += 1
                logger.info(f"Removed document: {doc.name} ({doc.document_id})")
        
        logger.info(f"Sync summary: {added_count} added, {updated_count} updated, {removed_count} removed")
        
        session.commit()
        documents = session.query(Document).all()
        logger.info(f"Returning {len(documents)} documents from database")
        return documents
    
    except Exception as e:
        logger.error(f"Error during document synchronization: {e}", exc_info=True)
        session.rollback()
        # Re-raise to let the caller handle it
        raise
    
    finally:
        session.close()


def get_user_conversations(telegram_id: int, limit: int = 10) -> List[Conversation]:
    """
    Get recent conversations for a user.
    
    Args:
        telegram_id: The Telegram user ID
        limit: Maximum number of conversations to return
        
    Returns:
        List[Conversation]: List of conversations
    """
    session = get_session()
    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        session.close()
        return []
    
    conversations = session.query(Conversation)\
        .filter(Conversation.user_id == user.id)\
        .order_by(Conversation.last_message_at.desc())\
        .limit(limit)\
        .all()
    
    session.close()
    return conversations


def get_or_create_conversation(telegram_id: int, document_id: Optional[str] = None) -> Tuple[Conversation, bool]:
    """
    Get the current conversation for a user or create a new one.
    
    Args:
        telegram_id: The Telegram user ID
        document_id: Optional document ID to associate with the conversation
        
    Returns:
        Tuple[Conversation, bool]: The conversation and a flag indicating if it was created
    """
    session = get_session()
    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        session.close()
        raise ValueError(f"User with Telegram ID {telegram_id} not found")
    
    # Get the most recent active conversation
    conversation = session.query(Conversation)\
        .filter(Conversation.user_id == user.id)\
        .order_by(Conversation.last_message_at.desc())\
        .first()
    
    created = False
    
    # If no conversation exists or we're switching documents, create a new one
    if not conversation or (document_id and conversation.document and 
                           conversation.document.document_id != document_id):
        document = None
        if document_id:
            document = session.query(Document).filter(Document.document_id == document_id).first()
        
        conversation = Conversation(
            user_id=user.id,
            document_id=document.id if document else None,
            title=f"Conversation {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        session.add(conversation)
        session.commit()
        created = True
    
    # Update the last message time
    conversation.last_message_at = datetime.datetime.utcnow()
    session.commit()
    
    # If document ID provided, update the conversation's document
    if document_id and (not conversation.document or 
                        conversation.document.document_id != document_id):
        document = session.query(Document).filter(Document.document_id == document_id).first()
        if document:
            conversation.document_id = document.id
            session.commit()
    
    session.close()
    return conversation, created


def add_message(conversation_id: int, role: str, content: str, 
               metadata: Optional[Dict[str, Any]] = None) -> Message:
    """
    Add a message to a conversation.
    
    Args:
        conversation_id: The conversation ID
        role: The role of the message sender ('user' or 'assistant')
        content: The message content
        metadata: Optional metadata for the message
        
    Returns:
        Message: The created message
    """
    session = get_session()
    
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    
    if metadata:
        message.set_meta_info(metadata)
    
    session.add(message)
    
    # Update the conversation's last message time
    conversation = session.query(Conversation).get(conversation_id)
    conversation.last_message_at = datetime.datetime.utcnow()
    
    session.commit()
    session.close()
    
    return message


def get_conversation_messages(conversation_id: int, limit: int = 20) -> List[Message]:
    """
    Get messages from a conversation.
    
    Args:
        conversation_id: The conversation ID
        limit: Maximum number of messages to return
        
    Returns:
        List[Message]: List of messages
    """
    session = get_session()
    
    messages = session.query(Message)\
        .filter(Message.conversation_id == conversation_id)\
        .order_by(Message.created_at.asc())\
        .limit(limit)\
        .all()
    
    session.close()
    return messages


def get_document_by_id(document_id: str) -> Optional[Document]:
    """
    Get a document by its ID.
    
    Args:
        document_id: The document ID
        
    Returns:
        Optional[Document]: The document, or None if not found
    """
    session = get_session()
    document = session.query(Document).filter(Document.document_id == document_id).first()
    session.close()
    return document


def update_document_access(document_id: str) -> None:
    """
    Update the last accessed timestamp for a document.
    
    Args:
        document_id: The document ID
    """
    session = get_session()
    document = session.query(Document).filter(Document.document_id == document_id).first()
    
    if document:
        document.last_accessed = datetime.datetime.utcnow()
        session.commit()
    
    session.close()
