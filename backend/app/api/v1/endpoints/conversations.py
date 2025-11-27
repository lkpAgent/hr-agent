"""
Conversation management endpoints
"""
import uuid
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

    # Convert conversations to dict to avoid DetachedInstanceError
    result = []
    for conv in conversations:
        result.append({
            "id": conv.id,
            "user_id": conv.user_id,
            "title": conv.title,
            "description": conv.description,
            "status": conv.status,
            "message_count": conv.total_messages,  # Map total_messages to message_count for schema
            "meta_data": conv.meta_data,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at
        })

    return result


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
        conversation_data=conversation_data
    )

    # Convert to dict to avoid DetachedInstanceError
    return {
        "id": conversation.id,
        "user_id": conversation.user_id,
        "title": conversation.title,
        "description": conversation.description,
        "status": conversation.status,
        "message_count": conversation.total_messages,
        "meta_data": conversation.meta_data,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at
    }


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
    conversation = await conversation_service.get_conversation(uuid.UUID(conversation_id), current_user.id)

    
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
    
    # Convert to dict to avoid DetachedInstanceError
    return {
        "id": conversation.id,
        "user_id": conversation.user_id,
        "title": conversation.title,
        "description": conversation.description,
        "status": conversation.status,
        "message_count": conversation.total_messages,
        "meta_data": conversation.meta_data,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at
    }


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

    conversation = await conversation_service.get_conversation(uuid.UUID(conversation_id), current_user.id)
    
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
    
    updated_conversation = await conversation_service.update_conversation(conversation.id,current_user.id, conversation_update)
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

    conversation = await conversation_service.get_conversation(uuid.UUID(conversation_id), current_user.id)

    
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
    
    await conversation_service.delete_conversation(conversation.id,current_user.id)
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
    conversation = await conversation_service.get_conversation(uuid.UUID(conversation_id), current_user.id)

    
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
        conversation_id=uuid.UUID(conversation_id),
        skip=skip,
        limit=limit
    )

    # Convert messages to dict to avoid PydanticSerializationError
    result = []
    for message in messages:
        result.append({
            "id": message.id,
            "conversation_id": message.conversation_id,
            "content": message.content,
            "role": message.role,
            "model_name": message.model_name,
            "context": message.context,
            "meta_data": message.meta_data,
            "rating": message.rating,
            "feedback": message.feedback,
            "parent_message_id": message.parent_message_id,
            "created_at": message.created_at,
            "updated_at": message.updated_at
        })

    return result
