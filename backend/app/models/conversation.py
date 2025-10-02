"""
Conversation model for storing chat history and AI interactions
"""
from sqlalchemy import Column, String, Text, ForeignKey, JSON, Enum, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class MessageRole(str, enum.Enum):
    """Message role enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(str, enum.Enum):
    """Conversation status enumeration"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Conversation(BaseModel):
    """Conversation model for storing chat sessions"""
    
    __tablename__ = "conversations"
    
    # Basic information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE, nullable=False)
    
    # Metadata
    meta_data = Column(JSON, nullable=True)
    total_messages = Column(Integer, default=0, nullable=False)
    
    # Relationships
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="conversations")
    
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(title='{self.title}', user_id='{self.user_id}')>"


class Message(BaseModel):
    """Message model for storing individual messages in conversations"""
    
    __tablename__ = "messages"
    
    model_config = {"protected_namespaces": ()}
    
    # Content
    content = Column(Text, nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    
    # AI-specific fields
    model_name = Column(String(100), nullable=True)  # e.g., "gpt-3.5-turbo"
    tokens_used = Column(Integer, nullable=True)
    response_time = Column(Float, nullable=True)  # Response time in seconds
    
    # Additional context and metadata
    context = Column(JSON, nullable=True)  # Additional context used for generation
    meta_data = Column(JSON, nullable=True)  # Message-specific metadata
    
    # Feedback
    rating = Column(Integer, nullable=True)  # User rating (1-5)
    feedback = Column(Text, nullable=True)  # User feedback
    
    # Relationships
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    conversation = relationship("Conversation", back_populates="messages")
    
    parent_message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    parent_message = relationship("Message", remote_side="Message.id")
    
    def __repr__(self):
        return f"<Message(role='{self.role}', conversation_id='{self.conversation_id}')>"