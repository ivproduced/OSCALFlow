"""
Database Models - SQLAlchemy ORM
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from core.database import Base


class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="user")  # user, admin, analyst
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    metadata = Column(JSONB, default={})
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="uploaded_by_user", foreign_keys="Document.uploaded_by")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.username} ({self.email})>"


class Conversation(Base):
    """Conversation/chat session model"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500))
    model = Column(String(100))  # Which LLM model was used
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata = Column(JSONB, default={})
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation {self.id} - {self.title}>"


class Message(Base):
    """Individual message in a conversation"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    model = Column(String(100))  # Specific model for this message
    tokens_used = Column(Integer)
    rag_sources = Column(JSONB)  # References to RAG documents used
    guardrails_applied = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata = Column(JSONB, default={})
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message {self.id} - {self.role}>"


class Document(Base):
    """Uploaded document for RAG"""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_path = Column(String(1000))  # Storage path
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed = Column(Boolean, default=False)
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    chunk_count = Column(Integer, default=0)
    metadata = Column(JSONB, default={})
    
    # Relationships
    uploaded_by_user = relationship("User", back_populates="documents", foreign_keys=[uploaded_by])
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document {self.filename}>"


class DocumentChunk(Base):
    """Text chunk from a document with embeddings"""
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(String)  # Vector stored as string, pgvector will handle it
    token_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata = Column(JSONB, default={})
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk {self.id} - Doc {self.document_id}>"


class AuditLog(Base):
    """Audit log for FISMA compliance"""
    __tablename__ = "audit_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100))
    resource_id = Column(String(100))
    ip_address = Column(String(50))
    user_agent = Column(Text)
    status_code = Column(Integer)
    request_id = Column(String(100), index=True)
    request_method = Column(String(10))
    request_path = Column(String(500))
    duration_ms = Column(Float)
    details = Column(JSONB, default={})
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog {self.action} by {self.user_id} at {self.timestamp}>"


class AgentExecution(Base):
    """Track agent task executions"""
    __tablename__ = "agent_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    agent_type = Column(String(100), nullable=False)  # general, research, code
    task = Column(Text, nullable=False)
    status = Column(String(50), default="running")  # running, completed, failed, cancelled
    result = Column(Text)
    error = Column(Text)
    iterations = Column(Integer, default=0)
    tools_used = Column(JSONB, default=[])
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    metadata = Column(JSONB, default={})
    
    def __repr__(self):
        return f"<AgentExecution {self.id} - {self.agent_type}>"


class APIKey(Base):
    """API keys for programmatic access"""
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200))
    key_hash = Column(String(255), nullable=False, unique=True)
    key_prefix = Column(String(20))  # First few chars for identification
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))
    last_used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata = Column(JSONB, default={})
    
    def __repr__(self):
        return f"<APIKey {self.name} - {self.key_prefix}...>"
