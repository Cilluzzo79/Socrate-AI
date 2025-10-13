"""
Database models for the Memvid Chat system.
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json
from pathlib import Path
import sys

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from config.config import DATABASE_URL

Base = declarative_base()


class User(Base):
    """User model for storing user information."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50), nullable=True)
    username = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"


class Document(Base):
    """Document model for storing information about available Memvid documents."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(String(100), unique=True, index=True)
    name = Column(String(100))
    video_path = Column(String(255))
    index_path = Column(String(255))
    size_mb = Column(Float)
    added_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=True)
    meta_info = Column(Text, nullable=True)  # JSON string
    
    # Relationships
    conversations = relationship("Conversation", back_populates="document")
    
    def __repr__(self):
        return f"<Document(id={self.id}, document_id={self.document_id}, name={self.name})>"
    
    def set_meta_info(self, meta_dict):
        """Set meta_info as JSON string."""
        self.meta_info = json.dumps(meta_dict)
    
    def get_meta_info(self):
        """Get meta_info as dictionary."""
        if not self.meta_info:
            return {}
        return json.loads(self.meta_info)


class Conversation(Base):
    """Conversation model for storing conversation sessions."""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    title = Column(String(100), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    document = relationship("Document", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id={self.user_id}, title={self.title})>"


class Message(Base):
    """Message model for storing individual messages within a conversation."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String(20))  # 'user' or 'assistant'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    meta_info = Column(Text, nullable=True)  # JSON string for storing additional information
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, created_at={self.created_at})>"
    
    def set_meta_info(self, meta_dict):
        """Set meta_info as JSON string."""
        self.meta_info = json.dumps(meta_dict)
    
    def get_meta_info(self):
        """Get meta_info as dictionary."""
        if not self.meta_info:
            return {}
        return json.loads(self.meta_info)


# Database initialization
def init_db():
    """Initialize the database and create tables."""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    return engine


def get_session():
    """Get a database session."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == "__main__":
    # Create the database when run directly
    print(f"Initializing database at {DATABASE_URL}...")
    engine = init_db()
    print("Database initialized successfully.")
