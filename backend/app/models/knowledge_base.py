"""
Knowledge base model for organizing documents and information
"""
from sqlalchemy import Column, String, Text, JSON, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class KnowledgeBase(BaseModel):
    """Knowledge base model for organizing documents"""
    
    __tablename__ = "knowledge_bases"
    
    # Basic information
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Configuration
    is_public = Column(Boolean, default=False, nullable=False)
    is_searchable = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    meta_data = Column(JSON, nullable=True)
    document_count = Column(Integer, default=0, nullable=False)
    
    # Categorization
    category = Column(String(100), nullable=True)  # e.g., "HR Policies", "Employee Handbook"
    tags = Column(JSON, nullable=True)  # List of tags
    
    # Relationships
    documents = relationship("Document", back_populates="knowledge_base")
    
    def __repr__(self):
        return f"<KnowledgeBase(name='{self.name}', category='{self.category}')>"


class FAQ(BaseModel):
    """Frequently Asked Questions model"""
    
    __tablename__ = "faqs"
    
    # Content
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    
    # Categorization
    category = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)
    
    # Metadata
    view_count = Column(Integer, default=0, nullable=False)
    helpful_count = Column(Integer, default=0, nullable=False)
    not_helpful_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=True)
    knowledge_base = relationship("KnowledgeBase")
    
    def __repr__(self):
        return f"<FAQ(question='{self.question[:50]}...', category='{self.category}')>"