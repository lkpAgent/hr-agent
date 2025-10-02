"""
Chat service for handling AI conversations
"""
import logging
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm_service import LLMService
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.schemas.chat import ChatResponse
from app.models.conversation import MessageRole

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat interactions"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_service = LLMService()
        self.conversation_service = ConversationService(db)
        self.document_service = DocumentService(db)
    
    async def process_message(
        self,
        user_id: UUID,
        conversation_id: UUID,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """
        Process a user message and generate AI response
        """
        try:
            # Save user message
            user_message = await self.conversation_service.add_message(
                conversation_id=conversation_id,
                content=message,
                role=MessageRole.USER
            )
            
            # Get conversation history
            history = await self.conversation_service.get_conversation_messages(
                conversation_id=conversation_id,
                limit=20
            )
            
            # Convert history to format expected by LLM
            conversation_history = []
            for msg in history[:-1]:  # Exclude the current message
                conversation_history.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
            
            # Search for relevant documents if needed
            relevant_context = ""
            if context and context.get("search_documents", True):
                search_results = await self.document_service.search_documents(
                    query=message,
                    user_id=user_id,
                    limit=3
                )
                if search_results:
                    relevant_context = "\n".join([
                        f"Document: {doc['filename']}\nContent: {doc['content'][:500]}..."
                        for doc in search_results
                    ])
            
            # Generate AI response
            ai_response = await self.llm_service.generate_response(
                message=message,
                conversation_history=conversation_history,
                context=relevant_context
            )
            
            # Save AI message
            ai_message = await self.conversation_service.add_message(
                conversation_id=conversation_id,
                content=ai_response,
                role=MessageRole.ASSISTANT,
                model_name=self.llm_service.chat_model.model_name,
                context={"relevant_documents": len(search_results) if 'search_results' in locals() else 0}
            )
            
            return ChatResponse(
                message_id=str(ai_message.id),
                conversation_id=str(conversation_id),
                content=ai_response,
                role=MessageRole.ASSISTANT,
                timestamp=ai_message.created_at,
                metadata={
                    "model_name": self.llm_service.chat_model.model_name,
                    "has_context": bool(relevant_context)
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise
    
    async def stream_message(
        self,
        user_id: UUID,
        conversation_id: UUID,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Process a message and stream the AI response
        """
        try:
            # Save user message
            user_message = await self.conversation_service.add_message(
                conversation_id=conversation_id,
                content=message,
                role=MessageRole.USER
            )
            
            # Get conversation history
            history = await self.conversation_service.get_conversation_messages(
                conversation_id=conversation_id,
                limit=20
            )
            
            # Convert history to format expected by LLM
            conversation_history = []
            for msg in history[:-1]:  # Exclude the current message
                conversation_history.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
            
            # Search for relevant documents if needed
            relevant_context = ""
            if context and context.get("search_documents", True):
                search_results = await self.document_service.search_documents(
                    query=message,
                    user_id=user_id,
                    limit=3
                )
                if search_results:
                    relevant_context = "\n".join([
                        f"Document: {doc['filename']}\nContent: {doc['content'][:500]}..."
                        for doc in search_results
                    ])
            
            # Stream AI response
            full_response = ""
            async for token in self.llm_service.stream_response(
                message=message,
                conversation_history=conversation_history,
                context=relevant_context
            ):
                full_response += token
                yield json.dumps({"token": token, "type": "token"})
            
            # Save complete AI message
            ai_message = await self.conversation_service.add_message(
                conversation_id=conversation_id,
                content=full_response,
                role=MessageRole.ASSISTANT,
                model_name=self.llm_service.chat_model.model_name,
                context={"relevant_documents": len(search_results) if 'search_results' in locals() else 0}
            )
            
            # Send completion signal
            yield json.dumps({
                "type": "complete",
                "message_id": str(ai_message.id),
                "timestamp": ai_message.created_at.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error streaming message: {e}")
            yield json.dumps({"type": "error", "error": str(e)})
    
    async def get_suggestions(self, query: str, user_id: UUID) -> List[str]:
        """
        Get AI-powered suggestions for user queries
        """
        try:
            # Get user's recent conversations for context
            recent_conversations = await self.conversation_service.get_user_conversations(
                user_id=user_id,
                limit=5
            )
            
            context = ""
            if recent_conversations:
                context = "Recent conversation topics: " + ", ".join([
                    conv.title for conv in recent_conversations
                ])
            
            suggestions = await self.llm_service.generate_suggestions(query, context)
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            return []
    
    async def submit_feedback(
        self,
        message_id: str,
        user_id: UUID,
        rating: int,
        feedback: str = ""
    ) -> None:
        """
        Submit feedback for a chat message
        """
        try:
            await self.conversation_service.update_message_feedback(
                message_id=message_id,
                rating=rating,
                feedback=feedback
            )
            
            logger.info(f"Feedback submitted for message {message_id} by user {user_id}")
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            raise