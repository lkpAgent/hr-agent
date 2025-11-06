"""
Document service for managing document upload, processing, and vector search
"""
import logging
import os
import hashlib
from typing import List, Optional, Dict, Any, BinaryIO
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc, func
from sqlalchemy.orm import selectinload

from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.services.llm_service import LLMService
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for managing documents and vector search"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_service = LLMService()
    
    async def upload_document(
        self,
        user_id: UUID,
        file: BinaryIO,
        filename: str,
        knowledge_base_id: Optional[UUID] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Document:
        """Upload and process a document"""
        try:
            # Read file content
            file_content = file.read()
            file_size = len(file_content)
            
            # Generate file hash for deduplication
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Check if document already exists
            existing_doc = await self._get_document_by_hash(file_hash, user_id)
            if existing_doc:
                logger.info(f"Document with hash {file_hash} already exists")
                return existing_doc
            
            # Determine MIME type
            mime_type = self._get_mime_type(filename)
            
            # Extract text content
            extracted_content = await self._extract_text_content(file_content, mime_type)
            
            # Generate summary
            summary = await self.llm_service.summarize_text(extracted_content[:2000])
            
            # Generate embedding for the document
            embedding = await self.llm_service.generate_embedding(
                f"{filename} {extracted_content[:1000]}"
            )
            
            # Save file to storage
            file_path = await self._save_file(file_content, filename, user_id)
            
            # Create document record
            document = Document(
                user_id=user_id,
                knowledge_base_id=knowledge_base_id,
                filename=filename,
                file_path=file_path,
                file_size=file_size,
                file_hash=file_hash,
                mime_type=mime_type,
                extracted_content=extracted_content,
                summary=summary,
                embedding=embedding,
                category=category,
                tags=tags or [],
                meta_data={
                    "upload_method": "api",
                    "processing_status": "completed"
                }
            )
            
            self.db.add(document)
            await self.db.commit()
            await self.db.refresh(document)
            
            # Process document into chunks for better search
            await self._create_document_chunks(document)
            
            logger.info(f"Uploaded document {document.id} for user {user_id}")
            return document
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error uploading document: {e}")
            raise
    
    async def get_document(
        self,
        document_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Optional[Document]:
        """Get a document by ID"""
        try:
            query = select(Document).where(Document.id == document_id)
            
            if user_id:
                query = query.where(Document.user_id == user_id)
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {e}")
            raise
    
    async def get_user_documents(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        knowledge_base_id: Optional[UUID] = None
    ) -> List[Document]:
        """Get documents for a user"""
        try:
            query = select(Document).where(Document.user_id == user_id)
            
            if category:
                query = query.where(Document.category == category)
            
            if knowledge_base_id:
                query = query.where(Document.knowledge_base_id == knowledge_base_id)
            
            query = query.order_by(desc(Document.created_at)).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting documents for user {user_id}: {e}")
            raise
    
    async def update_document(
        self,
        document_id: UUID,
        user_id: UUID,
        document_data: DocumentUpdate
    ) -> Optional[Document]:
        """Update a document"""
        try:
            # Check if document exists and belongs to user
            document = await self.get_document(document_id, user_id)
            if not document:
                return None
            
            update_data = document_data.dict(exclude_unset=True)
            if update_data:
                query = (
                    update(Document)
                    .where(Document.id == document_id)
                    .values(**update_data)
                )
                await self.db.execute(query)
                await self.db.commit()
                await self.db.refresh(document)
            
            logger.info(f"Updated document {document_id}")
            return document
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating document {document_id}: {e}")
            raise
    
    async def delete_document(
        self,
        document_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete a document and its chunks"""
        try:
            # Check if document exists and belongs to user
            document = await self.get_document(document_id, user_id)
            if not document:
                return False
            
            # Delete file from storage
            if document.file_path and os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            # Delete document chunks from langchain_pg_embedding table
            from sqlalchemy import text
            delete_query = text("""
                DELETE FROM langchain_pg_embedding 
                WHERE cmetadata->>'document_id' = :document_id
            """)
            await self.db.execute(delete_query, {"document_id": str(document_id)})
            
            # Delete document
            await self.db.execute(
                delete(Document).where(Document.id == document_id)
            )
            
            await self.db.commit()
            logger.info(f"Deleted document {document_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting document {document_id}: {e}")
            raise
    
    async def search_documents(
        self,
        query: str,
        user_id: UUID,
        limit: int = 10,
        knowledge_base_id: Optional[UUID] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search documents using vector similarity"""
        try:
            # Generate query embedding
            query_embedding = await self.llm_service.generate_embedding(query)
            
            # Build base query
            base_query = select(Document).where(Document.user_id == user_id)
            
            if knowledge_base_id:
                base_query = base_query.where(Document.knowledge_base_id == knowledge_base_id)
            
            if category:
                base_query = base_query.where(Document.category == category)
            
            # For now, we'll do a simple text search
            # In production, you'd use pgvector for similarity search
            text_query = base_query.where(
                Document.extracted_content.ilike(f"%{query}%")
            ).limit(limit)
            
            result = await self.db.execute(text_query)
            documents = result.scalars().all()
            
            # Format results
            search_results = []
            for doc in documents:
                search_results.append({
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "content": doc.extracted_content[:500],
                    "summary": doc.summary,
                    "category": doc.category,
                    "tags": doc.tags,
                    "created_at": doc.created_at.isoformat()
                })
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            raise
    
    async def _get_document_by_hash(
        self,
        file_hash: str,
        user_id: UUID
    ) -> Optional[Document]:
        """Get document by file hash"""
        query = select(Document).where(
            Document.file_hash == file_hash,
            Document.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    def _get_mime_type(self, filename: str) -> str:
        """Determine MIME type from filename"""
        extension = filename.lower().split('.')[-1]
        mime_types = {
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain',
            'md': 'text/markdown',
            'html': 'text/html',
            'json': 'application/json',
            'csv': 'text/csv'
        }
        return mime_types.get(extension, 'application/octet-stream')
    
    async def _extract_text_content(self, file_content: bytes, mime_type: str) -> str:
        """Extract text content from file"""
        try:
            if mime_type == 'text/plain':
                return file_content.decode('utf-8')
            elif mime_type == 'application/json':
                return file_content.decode('utf-8')
            elif mime_type == 'text/csv':
                return file_content.decode('utf-8')
            else:
                # For other types, return a placeholder
                # In production, you'd use libraries like PyPDF2, python-docx, etc.
                return f"Content extracted from {mime_type} file"
                
        except Exception as e:
            logger.error(f"Error extracting text content: {e}")
            return "Error extracting content"
    
    async def _save_file(self, file_content: bytes, filename: str, user_id: UUID) -> str:
        """Save file to storage"""
        try:
            # Create user directory
            user_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            
            # Generate unique filename
            file_hash = hashlib.sha256(file_content).hexdigest()[:8]
            name, ext = os.path.splitext(filename)
            unique_filename = f"{name}_{file_hash}{ext}"
            
            file_path = os.path.join(user_dir, unique_filename)
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise
    
    # NOTE: _create_document_chunks method removed - now using langchain_pg_embedding directly
    # Document chunks are created through PGVector in enhanced_document_service.py