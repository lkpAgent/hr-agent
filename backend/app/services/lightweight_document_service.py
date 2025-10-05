"""
Lightweight document service for basic document operations without LLM initialization
"""
import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.document import Document

logger = logging.getLogger(__name__)


class LightweightDocumentService:
    """Lightweight service for basic document operations without LLM dependencies"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        logger.info("Lightweight document service initialized")

    async def get_user_documents(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        knowledge_base_id: Optional[UUID] = None
    ) -> List[Document]:
        """Get user documents with optional filtering - optimized for performance"""
        try:
            query = select(Document).where(Document.user_id == user_id)
            
            if category:
                query = query.where(Document.category == category)
            
            if knowledge_base_id:
                query = query.where(Document.knowledge_base_id == knowledge_base_id)
            
            query = query.offset(skip).limit(limit).order_by(desc(Document.created_at))
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting user documents: {e}")
            raise

    async def get_by_id(self, document_id: str) -> Optional[Document]:
        """Get document by ID"""
        try:
            query = select(Document).where(Document.id == UUID(document_id))
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {e}")
            return None

    async def delete_document(self, document_id: str) -> bool:
        """Delete document by ID"""
        try:
            document = await self.get_by_id(document_id)
            if not document:
                return False
            
            await self.db.delete(document)
            await self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            raise