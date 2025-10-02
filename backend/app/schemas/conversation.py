"""
Conversation-related Pydantic schemas
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.conversation import MessageRole, ConversationStatus


class ConversationBase(BaseModel):
    """Base conversation schema"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    meta_data: Optional[Dict[str, Any]] = None


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation"""
    pass


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[ConversationStatus] = None
    meta_data: Optional[Dict[str, Any]] = None


class ConversationInDB(ConversationBase):
    """Schema for conversation in database"""
    id: UUID
    user_id: UUID
    status: ConversationStatus
    message_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Conversation(ConversationInDB):
    """Public conversation schema"""
    pass


class MessageBase(BaseModel):
    """Base message schema"""
    model_config = {"protected_namespaces": ()}
    
    content: str = Field(..., min_length=1)
    role: MessageRole
    model_name: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class MessageCreate(MessageBase):
    """Schema for creating a message"""
    conversation_id: UUID
    parent_id: Optional[UUID] = None


class MessageUpdate(BaseModel):
    """Schema for updating a message"""
    content: Optional[str] = Field(None, min_length=1)
    user_feedback: Optional[Dict[str, Any]] = None


class MessageInDB(MessageBase):
    """Schema for message in database"""
    id: UUID
    conversation_id: UUID
    parent_id: Optional[UUID]
    user_feedback: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Message(MessageInDB):
    """Public message schema"""
    pass


class ConversationWithMessages(Conversation):
    """Conversation schema with messages"""
    messages: List[Message] = []


class MessageFeedback(BaseModel):
    """Schema for message feedback"""
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = Field(None, max_length=500)