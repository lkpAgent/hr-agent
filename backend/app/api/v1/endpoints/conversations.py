"""
Conversation management endpoints
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.conversation import Conversation as ConversationSchema, ConversationCreate, ConversationUpdate
from app.schemas.user import User as UserSchema
from app.services.conversation_service import ConversationService
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/", response_model=List[ConversationSchema])
async def get_conversations(
    skip: int = 0,
    limit: int = 100,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get user's conversations
    """
    conversation_service = ConversationService(db)
    conversations = await conversation_service.get_user_conversations(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return conversations


@router.post("/", response_model=ConversationSchema)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new conversation
    """
    conversation_service = ConversationService(db)
    conversation = await conversation_service.create_conversation(
        user_id=current_user.id,
        title=conversation_data.title,
        description=conversation_data.description
    )
    return conversation


@router.get("/{conversation_id}", response_model=ConversationSchema)
async def get_conversation(
    conversation_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get conversation by ID
    """
    conversation_service = ConversationService(db)
    conversation = await conversation_service.get_by_id(conversation_id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return conversation


@router.put("/{conversation_id}", response_model=ConversationSchema)
async def update_conversation(
    conversation_id: str,
    conversation_update: ConversationUpdate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update conversation
    """
    conversation_service = ConversationService(db)
    conversation = await conversation_service.get_by_id(conversation_id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    updated_conversation = await conversation_service.update(conversation, conversation_update)
    return updated_conversation


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete conversation
    """
    conversation_service = ConversationService(db)
    conversation = await conversation_service.get_by_id(conversation_id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    await conversation_service.delete(conversation)
    return {"message": "Conversation deleted successfully"}


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get messages from a conversation
    """
    conversation_service = ConversationService(db)
    conversation = await conversation_service.get_by_id(conversation_id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    messages = await conversation_service.get_conversation_messages(
        conversation_id=conversation_id,
        skip=skip,
        limit=limit
    )
    return messages