"""
Multi-tenant Database Models for Socrate AI
SQLAlchemy models for PostgreSQL on Railway
"""

from sqlalchemy import create_engine, Column, String, Integer, BigInteger, Text, TIMESTAMP, ForeignKey, Boolean, JSON, TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import uuid
from datetime import datetime
import os

# Database URL from environment (Railway provides this)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///socrate_ai_dev.db')

# For Railway PostgreSQL compatibility
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


# ============================================================================
# CROSS-DATABASE UUID TYPE
# ============================================================================

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            else:
                return value


# ============================================================================
# MODELS
# ============================================================================

class User(Base):
    """User model - linked to Telegram account"""
    __tablename__ = 'users'

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255))
    photo_url = Column(Text)
    email = Column(String(255))

    # Subscription management
    subscription_tier = Column(String(20), default='free')  # free, pro, enterprise
    storage_quota_mb = Column(Integer, default=500)
    storage_used_mb = Column(Integer, default=0)

    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    last_login = Column(TIMESTAMP)

    # Settings (JSON/JSONB for flexibility - use JSON for SQLite compatibility)
    settings = Column(JSON, default={})

    # Relationships
    documents = relationship('Document', back_populates='user', cascade='all, delete-orphan')
    chat_sessions = relationship('ChatSession', back_populates='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, first_name='{self.first_name}')>"


class Document(Base):
    """Document model - user-owned files"""
    __tablename__ = 'documents'
    __mapper_args__ = {
        'exclude_properties': ['file_data']  # Ignore file_data column in DB
    }

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    mime_type = Column(String(50))
    file_size = Column(BigInteger)  # bytes
    file_path = Column(Text)  # /storage/{user_id}/{doc_id}/file.ext

    # Processing status
    status = Column(String(20), default='processing')  # uploading, processing, ready, failed
    processing_progress = Column(Integer, default=0)  # 0-100%
    error_message = Column(Text)

    # Content metadata
    language = Column(String(10))  # it, en, es, etc.
    total_chunks = Column(Integer)
    total_tokens = Column(Integer)
    duration_seconds = Column(Integer)  # for videos
    page_count = Column(Integer)  # for PDFs

    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    processing_started_at = Column(TIMESTAMP)
    processing_completed_at = Column(TIMESTAMP)

    # Additional metadata (flexible JSON/JSONB) - renamed to avoid SQLAlchemy conflict
    doc_metadata = Column(JSON, default={})

    # Relationships
    user = relationship('User', back_populates='documents')
    chat_sessions = relationship('ChatSession', back_populates='document')

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}')>"


class ChatSession(Base):
    """Chat session - tracks all user interactions"""
    __tablename__ = 'chat_sessions'

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    document_id = Column(GUID, ForeignKey('documents.id', ondelete='SET NULL'), index=True)

    # Request information
    command_type = Column(String(20), nullable=False, index=True)  # quiz, summary, analyze, outline, mindmap
    request_data = Column(JSON, nullable=False)  # Input parameters

    # Response information
    response_data = Column(JSON)  # Generated output
    response_format = Column(String(10))  # markdown, html, json

    # Metadata
    channel = Column(String(20), nullable=False)  # telegram, web_app, api
    llm_model = Column(String(50))  # gpt-4, claude-3, etc.
    tokens_used = Column(Integer)
    generation_time_ms = Column(Integer)

    # Success tracking
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    # Timestamp
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship('User', back_populates='chat_sessions')
    document = relationship('Document', back_populates='chat_sessions')

    def __repr__(self):
        return f"<ChatSession(id={self.id}, command_type='{self.command_type}', channel='{self.channel}')>"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_db():
    """
    Get database session (use with context manager)

    Usage:
        with get_db() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database (create all tables)"""
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Database initialized successfully")
        print(f"     Tables created: {', '.join(Base.metadata.tables.keys())}")
        return True
    except Exception as e:
        print(f"[ERROR] Error initializing database: {e}")
        return False


def reset_db():
    """Reset database (drop and recreate all tables) - USE WITH CAUTION!"""
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("[OK] Database reset successfully")
        return True
    except Exception as e:
        print("[ERROR] Error resetting database: {e}")
        return False


# ============================================================================
# USER OPERATIONS
# ============================================================================

def get_or_create_user(telegram_id: int, first_name: str, **kwargs) -> User:
    """
    Get existing user or create new one

    Args:
        telegram_id: Telegram user ID
        first_name: User's first name
        **kwargs: Additional user fields (username, last_name, photo_url, email)

    Returns:
        User object
    """
    db = SessionLocal()
    try:
        # Try to find existing user
        user = db.query(User).filter_by(telegram_id=telegram_id).first()

        if user:
            # Update last login and any changed fields
            user.last_login = datetime.utcnow()
            for key, value in kwargs.items():
                if hasattr(user, key) and value is not None:
                    setattr(user, key, value)
            db.commit()
            db.refresh(user)
            return user

        # Create new user
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            last_login=datetime.utcnow(),
            **kwargs
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    finally:
        db.close()


def get_user_by_telegram_id(telegram_id: int) -> User:
    """Get user by Telegram ID"""
    db = SessionLocal()
    try:
        return db.query(User).filter_by(telegram_id=telegram_id).first()
    finally:
        db.close()


def get_user_by_id(user_id: str) -> User:
    """Get user by UUID"""
    db = SessionLocal()
    try:
        return db.query(User).filter_by(id=uuid.UUID(user_id)).first()
    finally:
        db.close()


# Auto-initialize database on import (if not exists)
if __name__ == '__main__':
    init_db()
