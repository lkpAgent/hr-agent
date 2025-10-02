"""
Chat endpoints for HR Agent AI interactions
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.chat import ChatMessage, ChatResponse, ChatRequest
from app.schemas.user import User as UserSchema
from app.services.chat_service import ChatService
from app.services.conversation_service import ConversationService
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/send", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Send a message to the HR Agent and get a response
    """
    chat_service = ChatService(db)
    conversation_service = ConversationService(db)
    
    try:
        # Get or create conversation
        if chat_request.conversation_id:
            conversation = await conversation_service.get_by_id(chat_request.conversation_id)
            if not conversation or conversation.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
        else:
            # Create new conversation
            conversation = await conversation_service.create_conversation(
                user_id=current_user.id,
                title=chat_request.message[:50] + "..." if len(chat_request.message) > 50 else chat_request.message
            )
        
        # Process the message and get AI response
        response = await chat_service.process_message(
            user_id=current_user.id,
            conversation_id=conversation.id,
            message=chat_request.message,
            context=chat_request.context
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@router.post("/stream")
async def stream_message(
    chat_request: ChatRequest,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message and get a streaming response
    """
    chat_service = ChatService(db)
    conversation_service = ConversationService(db)
    
    try:
        # Get or create conversation
        if chat_request.conversation_id:
            conversation = await conversation_service.get_by_id(chat_request.conversation_id)
            if not conversation or conversation.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
        else:
            # Create new conversation
            conversation = await conversation_service.create_conversation(
                user_id=current_user.id,
                title=chat_request.message[:50] + "..." if len(chat_request.message) > 50 else chat_request.message
            )
        
        # Get streaming response
        async def generate_response():
            async for chunk in chat_service.stream_message(
                user_id=current_user.id,
                conversation_id=conversation.id,
                message=chat_request.message,
                context=chat_request.context
            ):
                yield f"data: {chunk}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing streaming message: {str(e)}"
        )


@router.get("/suggestions")
async def get_suggestions(
    query: str = "",
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[str]:
    """
    Get AI-powered suggestions for user queries
    """
    chat_service = ChatService(db)
    
    try:
        suggestions = await chat_service.get_suggestions(query, current_user.id)
        return suggestions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting suggestions: {str(e)}"
        )


@router.post("/feedback")
async def submit_feedback(
    message_id: str,
    rating: int,
    feedback: str = "",
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Submit feedback for a chat message
    """
    chat_service = ChatService(db)
    
    try:
        await chat_service.submit_feedback(
            message_id=message_id,
            user_id=current_user.id,
            rating=rating,
            feedback=feedback
        )
        
        return {"message": "Feedback submitted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting feedback: {str(e)}"
        )