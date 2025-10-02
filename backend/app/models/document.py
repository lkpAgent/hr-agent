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
    mime_type = Column(String(100), nullable=False)
    
    # Content and metadata
    content = Column(Text, nullable=True)  # Extracted text content
    summary = Column(Text, nullable=True)  # AI-generated summary
    meta_data = Column(JSON, nullable=True)  # Additional metadata
    
    # Vector embedding for semantic search
    embedding = Column(Vector(settings.VECTOR_DIMENSION), nullable=True)
    
    # Categorization
    category = Column(String(100), nullable=True)  # e.g., "policy", "handbook", "form"
    tags = Column(JSON, nullable=True)  # List of tags
    
    # Relationships
    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    uploaded_by = relationship("User", back_populates="documents")
    
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=True)
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    
    def __repr__(self):
        return f"<Document(filename='{self.filename}', category='{self.category}')>"


class DocumentChunk(BaseModel):
    """Document chunks for better vector search and retrieval"""
    
    __tablename__ = "document_chunks"
    
    # Content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_size = Column(Integer, nullable=False)
    
    # Vector embedding
    embedding = Column(Vector(settings.VECTOR_DIMENSION), nullable=True)
    
    # Metadata
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    document = relationship("Document")
    
    def __repr__(self):
        return f"<DocumentChunk(document_id='{self.document_id}', chunk_index={self.chunk_index})>"