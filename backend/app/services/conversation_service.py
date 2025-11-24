"""
Conversation service for managing conversations and messages
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc, func
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, Message, MessageRole, ConversationStatus
from app.schemas.conversation import ConversationCreate, ConversationUpdate, MessageCreate

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations and messages"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_conversation(
        self,
        user_id: UUID,
        conversation_data: ConversationCreate
    ) -> Conversation:
        """Create a new conversation"""
        try:
            conversation = Conversation(
                user_id=user_id,
                title=conversation_data.title,
                description=conversation_data.description,
                status=ConversationStatus.ACTIVE,
                meta_data=conversation_data.meta_data or {}
            )
            
            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)
            
            logger.info(f"Created conversation {conversation.id} for user {user_id}")
            return conversation
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating conversation: {e}")
            raise
    
    async def get_conversation(
        self,
        conversation_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Optional[Conversation]:
        """Get a conversation by ID"""
        try:
            query = select(Conversation).where(Conversation.id == conversation_id)
            
            if user_id:
                query = query.where(Conversation.user_id == user_id)
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {e}")
            raise
    
    async def get_user_conversations(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: Optional[ConversationStatus] = None
    ) -> List[Conversation]:
        """Get conversations for a user"""
        try:
            query = select(Conversation).where(Conversation.user_id == user_id)
            
            if status:
                query = query.where(Conversation.status == status)
            
            query = query.order_by(desc(Conversation.updated_at)).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting conversations for user {user_id}: {e}")
            raise
    
    async def update_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
        conversation_data: ConversationUpdate
    ) -> Optional[Conversation]:
        """Update a conversation"""
        try:
            # Check if conversation exists and belongs to user
            conversation = await self.get_conversation(conversation_id, user_id)
            if not conversation:
                return None
            
            update_data = conversation_data.dict(exclude_unset=True)
            if update_data:
                query = (
                    update(Conversation)
                    .where(Conversation.id == conversation_id)
                    .values(**update_data)
                )
                await self.db.execute(query)
                await self.db.commit()
                await self.db.refresh(conversation)
            
            logger.info(f"Updated conversation {conversation_id}")
            return conversation
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating conversation {conversation_id}: {e}")
            raise
    
    async def delete_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete a conversation and its messages"""
        try:
            # Check if conversation exists and belongs to user
            conversation = await self.get_conversation(conversation_id, user_id)
            if not conversation:
                return False
            
            # Delete all messages first
            await self.db.execute(
                delete(Message).where(Message.conversation_id == conversation_id)
            )
            
            # Delete conversation
            await self.db.execute(
                delete(Conversation).where(Conversation.id == conversation_id)
            )
            
            await self.db.commit()
            logger.info(f"Deleted conversation {conversation_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            raise
    
    async def add_message(
        self,
        conversation_id: UUID,
        content: str,
        role: MessageRole,
        model_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        parent_id: Optional[UUID] = None
    ) -> Message:
        """Add a message to a conversation"""
        try:
            message = Message(
                conversation_id=conversation_id,
                content=content,
                role=role,
                model_name=model_name,
                context=context or {},
                parent_id=parent_id
            )
            
            self.db.add(message)
            
            # Update conversation message count and last activity
            await self.db.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(
                    message_count=Conversation.message_count + 1,
                    updated_at=func.now()
                )
            )
            
            await self.db.commit()
            await self.db.refresh(message)
            
            logger.info(f"Added message to conversation {conversation_id}")
            return message
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error adding message to conversation {conversation_id}: {e}")
            raise
    
    async def get_conversation_messages(
        self,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[Message]:
        """Get messages for a conversation"""
        try:
            query = (
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
                .offset(skip)
                .limit(limit)
            )
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting messages for conversation {conversation_id}: {e}")
            raise
    
    async def get_message(self, message_id: UUID) -> Optional[Message]:
        """Get a message by ID"""
        try:
            query = select(Message).where(Message.id == message_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting message {message_id}: {e}")
            raise
    
    async def update_message_feedback(
        self,
        message_id: str,
        rating: int,
        feedback: str = ""
    ) -> bool:
        """Update message feedback"""
        try:
            message_uuid = UUID(message_id)
            query = (
                update(Message)
                .where(Message.id == message_uuid)
                .values(
                    user_feedback={
                        "rating": rating,
                        "feedback": feedback
                    }
                )
            )
            
            result = await self.db.execute(query)
            await self.db.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating message feedback {message_id}: {e}")
            raise
    
    async def search_conversations(
        self,
        user_id: UUID,
        query: str,
        limit: int = 10
    ) -> List[Conversation]:
        """Search conversations by title or content"""
        try:
            # Simple text search - in production, you might want to use full-text search
            search_query = (
                select(Conversation)
                .where(
                    Conversation.user_id == user_id,
                    Conversation.title.ilike(f"%{query}%")
                )
                .order_by(desc(Conversation.updated_at))
                .limit(limit)
            )
            
            result = await self.db.execute(search_query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching conversations for user {user_id}: {e}")
            raise