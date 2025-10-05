"""
Knowledge base service for managing knowledge bases and FAQs
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc, func

from app.models.knowledge_base import KnowledgeBase, FAQ
from app.models.document import Document
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate, FAQCreate, FAQUpdate

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """Service for managing knowledge bases and FAQs"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_knowledge_base(
        self,
        kb_data: KnowledgeBaseCreate
    ) -> KnowledgeBase:
        """Create a new knowledge base"""
        try:
            knowledge_base = KnowledgeBase(
                name=kb_data.name,
                description=kb_data.description,
                is_public=kb_data.is_public,
                is_searchable=kb_data.is_searchable,
                category=kb_data.category,
                tags=kb_data.tags or [],
                meta_data=kb_data.meta_data or {}
            )
            
            self.db.add(knowledge_base)
            await self.db.commit()
            await self.db.refresh(knowledge_base)
            
            logger.info(f"Created knowledge base {knowledge_base.id}")
            return knowledge_base
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating knowledge base: {e}")
            raise
    
    async def get_knowledge_base(self, kb_id: UUID) -> Optional[KnowledgeBase]:
        """Get a knowledge base by ID"""
        try:
            query = select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting knowledge base {kb_id}: {e}")
            raise
    
    async def get_knowledge_bases(
        self,
        skip: int = 0,
        limit: int = 20,
        is_public: Optional[bool] = None,
        category: Optional[str] = None
    ) -> List[KnowledgeBase]:
        """Get knowledge bases with optional filtering"""
        try:
            query = select(KnowledgeBase)
            
            if is_public is not None:
                query = query.where(KnowledgeBase.is_public == is_public)
            
            if category:
                query = query.where(KnowledgeBase.category == category)
            
            query = query.order_by(desc(KnowledgeBase.created_at)).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting knowledge bases: {e}")
            raise
    
    async def get_accessible_knowledge_bases(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[KnowledgeBase]:
        """Get knowledge bases accessible to a user"""
        try:
            # For now, return all public knowledge bases
            # In the future, this could include user-specific access control
            query = select(KnowledgeBase).where(
                KnowledgeBase.is_public == True
            ).order_by(desc(KnowledgeBase.created_at)).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting accessible knowledge bases for user {user_id}: {e}")
            raise
    
    async def create(self, kb_data: KnowledgeBaseCreate) -> KnowledgeBase:
        """Create a new knowledge base (alias for create_knowledge_base)"""
        return await self.create_knowledge_base(kb_data)
    
    async def get_by_id(self, kb_id: str) -> Optional[KnowledgeBase]:
        """Get a knowledge base by ID (alias for get_knowledge_base)"""
        try:
            kb_uuid = UUID(kb_id)
            return await self.get_knowledge_base(kb_uuid)
        except ValueError:
            logger.error(f"Invalid UUID format: {kb_id}")
            return None
    
    async def update(self, knowledge_base: KnowledgeBase, kb_update: KnowledgeBaseUpdate) -> KnowledgeBase:
        """Update a knowledge base"""
        return await self.update_knowledge_base(knowledge_base.id, kb_update)
    
    async def delete(self, knowledge_base: KnowledgeBase) -> bool:
        """Delete a knowledge base"""
        return await self.delete_knowledge_base(knowledge_base.id)
    
    async def update_knowledge_base(
        self,
        kb_id: UUID,
        kb_data: KnowledgeBaseUpdate
    ) -> Optional[KnowledgeBase]:
        """Update a knowledge base"""
        try:
            # Check if knowledge base exists
            kb = await self.get_knowledge_base(kb_id)
            if not kb:
                return None
            
            update_data = kb_data.dict(exclude_unset=True)
            if update_data:
                query = (
                    update(KnowledgeBase)
                    .where(KnowledgeBase.id == kb_id)
                    .values(**update_data)
                )
                await self.db.execute(query)
                await self.db.commit()
                await self.db.refresh(kb)
            
            logger.info(f"Updated knowledge base {kb_id}")
            return kb
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating knowledge base {kb_id}: {e}")
            raise
    
    async def delete_knowledge_base(self, kb_id: UUID) -> bool:
        """Delete a knowledge base and update related documents"""
        try:
            # Check if knowledge base exists
            kb = await self.get_knowledge_base(kb_id)
            if not kb:
                return False
            
            # Update documents to remove knowledge base reference
            await self.db.execute(
                update(Document)
                .where(Document.knowledge_base_id == kb_id)
                .values(knowledge_base_id=None)
            )
            
            # Delete related FAQs
            await self.db.execute(
                delete(FAQ).where(FAQ.knowledge_base_id == kb_id)
            )
            
            # Delete knowledge base
            await self.db.execute(
                delete(KnowledgeBase).where(KnowledgeBase.id == kb_id)
            )
            
            await self.db.commit()
            logger.info(f"Deleted knowledge base {kb_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting knowledge base {kb_id}: {e}")
            raise
    
    async def search_knowledge_base(
        self,
        kb_id: UUID,
        query: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search within a specific knowledge base"""
        try:
            # Get knowledge base
            kb = await self.get_knowledge_base(kb_id)
            if not kb:
                return {"documents": [], "faqs": []}
            
            # Search documents
            doc_query = (
                select(Document)
                .where(
                    Document.knowledge_base_id == kb_id,
                    Document.extracted_content.ilike(f"%{query}%")
                )
                .limit(limit)
            )
            doc_result = await self.db.execute(doc_query)
            documents = doc_result.scalars().all()
            
            # Search FAQs
            faq_query = (
                select(FAQ)
                .where(
                    FAQ.knowledge_base_id == kb_id,
                    (FAQ.question.ilike(f"%{query}%") | FAQ.answer.ilike(f"%{query}%"))
                )
                .limit(limit)
            )
            faq_result = await self.db.execute(faq_query)
            faqs = faq_result.scalars().all()
            
            return {
                "knowledge_base": {
                    "id": str(kb.id),
                    "name": kb.name,
                    "description": kb.description
                },
                "documents": [
                    {
                        "id": str(doc.id),
                        "filename": doc.filename,
                        "content": doc.extracted_content[:300],
                        "summary": doc.summary
                    }
                    for doc in documents
                ],
                "faqs": [
                    {
                        "id": str(faq.id),
                        "question": faq.question,
                        "answer": faq.answer,
                        "category": faq.category
                    }
                    for faq in faqs
                ]
            }
            
        except Exception as e:
            logger.error(f"Error searching knowledge base {kb_id}: {e}")
            raise
    
    async def get_knowledge_base_stats(self, kb_id: UUID) -> Dict[str, Any]:
        """Get statistics for a knowledge base"""
        try:
            # Get document count
            doc_count_query = select(func.count(Document.id)).where(
                Document.knowledge_base_id == kb_id
            )
            doc_count_result = await self.db.execute(doc_count_query)
            doc_count = doc_count_result.scalar()
            
            # Get FAQ count
            faq_count_query = select(func.count(FAQ.id)).where(
                FAQ.knowledge_base_id == kb_id
            )
            faq_count_result = await self.db.execute(faq_count_query)
            faq_count = faq_count_result.scalar()
            
            # Update knowledge base document count
            await self.db.execute(
                update(KnowledgeBase)
                .where(KnowledgeBase.id == kb_id)
                .values(document_count=doc_count)
            )
            await self.db.commit()
            
            return {
                "document_count": doc_count,
                "faq_count": faq_count
            }
            
        except Exception as e:
            logger.error(f"Error getting knowledge base stats {kb_id}: {e}")
            raise
    
    # FAQ Management
    async def create_faq(
        self,
        faq_data: FAQCreate,
        knowledge_base_id: Optional[UUID] = None
    ) -> FAQ:
        """Create a new FAQ"""
        try:
            faq = FAQ(
                knowledge_base_id=knowledge_base_id,
                question=faq_data.question,
                answer=faq_data.answer,
                category=faq_data.category,
                tags=faq_data.tags or [],
                meta_data=faq_data.metadata or {}
            )
            
            self.db.add(faq)
            await self.db.commit()
            await self.db.refresh(faq)
            
            logger.info(f"Created FAQ {faq.id}")
            return faq
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating FAQ: {e}")
            raise
    
    async def get_faq(self, faq_id: UUID) -> Optional[FAQ]:
        """Get an FAQ by ID"""
        try:
            query = select(FAQ).where(FAQ.id == faq_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting FAQ {faq_id}: {e}")
            raise
    
    async def get_faqs(
        self,
        skip: int = 0,
        limit: int = 20,
        knowledge_base_id: Optional[UUID] = None,
        category: Optional[str] = None
    ) -> List[FAQ]:
        """Get FAQs with optional filtering"""
        try:
            query = select(FAQ)
            
            if knowledge_base_id:
                query = query.where(FAQ.knowledge_base_id == knowledge_base_id)
            
            if category:
                query = query.where(FAQ.category == category)
            
            query = query.order_by(desc(FAQ.view_count), desc(FAQ.created_at)).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting FAQs: {e}")
            raise
    
    async def update_faq(
        self,
        faq_id: UUID,
        faq_data: FAQUpdate
    ) -> Optional[FAQ]:
        """Update an FAQ"""
        try:
            # Check if FAQ exists
            faq = await self.get_faq(faq_id)
            if not faq:
                return None
            
            update_data = faq_data.dict(exclude_unset=True)
            if update_data:
                query = (
                    update(FAQ)
                    .where(FAQ.id == faq_id)
                    .values(**update_data)
                )
                await self.db.execute(query)
                await self.db.commit()
                await self.db.refresh(faq)
            
            logger.info(f"Updated FAQ {faq_id}")
            return faq
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating FAQ {faq_id}: {e}")
            raise
    
    async def delete_faq(self, faq_id: UUID) -> bool:
        """Delete an FAQ"""
        try:
            # Check if FAQ exists
            faq = await self.get_faq(faq_id)
            if not faq:
                return False
            
            # Delete FAQ
            await self.db.execute(
                delete(FAQ).where(FAQ.id == faq_id)
            )
            
            await self.db.commit()
            logger.info(f"Deleted FAQ {faq_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting FAQ {faq_id}: {e}")
            raise
    
    async def increment_faq_view(self, faq_id: UUID) -> None:
        """Increment FAQ view count"""
        try:
            query = (
                update(FAQ)
                .where(FAQ.id == faq_id)
                .values(view_count=FAQ.view_count + 1)
            )
            await self.db.execute(query)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error incrementing FAQ view count {faq_id}: {e}")
    
    async def submit_faq_feedback(
        self,
        faq_id: UUID,
        is_helpful: bool
    ) -> None:
        """Submit feedback for an FAQ"""
        try:
            if is_helpful:
                query = (
                    update(FAQ)
                    .where(FAQ.id == faq_id)
                    .values(helpful_count=FAQ.helpful_count + 1)
                )
            else:
                query = (
                    update(FAQ)
                    .where(FAQ.id == faq_id)
                    .values(not_helpful_count=FAQ.not_helpful_count + 1)
                )
            
            await self.db.execute(query)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error submitting FAQ feedback {faq_id}: {e}")
    
    async def search_faqs(
        self,
        query: str,
        limit: int = 10,
        knowledge_base_id: Optional[UUID] = None
    ) -> List[FAQ]:
        """Search FAQs by question or answer"""
        try:
            search_query = select(FAQ).where(
                FAQ.question.ilike(f"%{query}%") | FAQ.answer.ilike(f"%{query}%")
            )
            
            if knowledge_base_id:
                search_query = search_query.where(FAQ.knowledge_base_id == knowledge_base_id)
            
            search_query = search_query.order_by(desc(FAQ.helpful_count)).limit(limit)
            
            result = await self.db.execute(search_query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching FAQs: {e}")
            raise