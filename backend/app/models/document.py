"""
Document model for file management and vector storage
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.models.base import BaseModel
from app.core.config import settings


class Document(BaseModel):
    """Document model for storing files and their metadata"""
    
    __tablename__ = "documents"
    
    # Basic information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA256 hash
    mime_type = Column(String(100), nullable=False)
    
    # Content and metadata
    extracted_content = Column(Text, nullable=True)  # Extracted text content
    summary = Column(Text, nullable=True)  # AI-generated summary
    meta_data = Column(JSON, nullable=True)  # Additional metadata
    
    # Vector embedding for semantic search
    embedding = Column(Vector(settings.VECTOR_DIMENSION), nullable=True)
    
    # Categorization
    category = Column(String(100), nullable=True)  # e.g., "policy", "handbook", "form"
    tags = Column(JSON, nullable=True)  # List of tags
    
    # Relationships
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    uploaded_by = relationship("User", back_populates="documents")
    
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=True)
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    
    def __repr__(self):
        return f"<Document at {hex(id(self))}>"


# DocumentChunk model removed - using langchain_pg_embedding table directly