"""
Document-related Pydantic schemas
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """Base document schema"""
    filename: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentCreate(DocumentBase):
    """Schema for creating a document"""
    knowledge_base_id: Optional[UUID] = None


class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    filename: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    knowledge_base_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentInDB(DocumentBase):
    """Schema for document in database"""
    id: UUID
    user_id: UUID
    knowledge_base_id: Optional[UUID]
    file_path: str
    file_size: int
    file_hash: str
    mime_type: str
    extracted_content: Optional[str]
    summary: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Document(DocumentInDB):
    """Public document schema"""
    pass


class DocumentUpload(BaseModel):
    """Schema for document upload"""
    knowledge_base_id: Optional[UUID] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None


class DocumentSearch(BaseModel):
    """Schema for document search"""
    query: str = Field(..., min_length=1, max_length=500)
    knowledge_base_id: Optional[UUID] = None
    category: Optional[str] = None
    limit: Optional[int] = Field(10, ge=1, le=50)


class DocumentSearchResult(BaseModel):
    """Schema for document search result"""
    id: str
    filename: str
    content: str
    summary: Optional[str]
    category: Optional[str]
    tags: List[str]
    created_at: str
    relevance_score: Optional[float] = None


class DocumentChunkBase(BaseModel):
    """Base document chunk schema"""
    content: str
    chunk_index: int
    chunk_size: int
    metadata: Optional[Dict[str, Any]] = None


class DocumentChunkInDB(DocumentChunkBase):
    """Schema for document chunk in database"""
    id: UUID
    document_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentChunk(DocumentChunkInDB):
    """Public document chunk schema"""
    pass