"""
Knowledge base management endpoints
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.knowledge_base import KnowledgeBase as KnowledgeBaseSchema, KnowledgeBaseCreate, KnowledgeBaseUpdate
from app.schemas.user import User as UserSchema
from app.services.knowledge_base_service import KnowledgeBaseService
from app.api.deps import get_current_user, get_current_superuser

router = APIRouter()


@router.get("/", response_model=List[KnowledgeBaseSchema])
async def get_knowledge_bases(
    skip: int = 0,
    limit: int = 100,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get knowledge bases
    """
    kb_service = KnowledgeBaseService(db)
    knowledge_bases = await kb_service.get_accessible_knowledge_bases(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return knowledge_bases


@router.post("/", response_model=KnowledgeBaseSchema)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new knowledge base
    """
    kb_service = KnowledgeBaseService(db)
    knowledge_base = await kb_service.create(kb_data)
    return knowledge_base


@router.get("/{kb_id}", response_model=KnowledgeBaseSchema)
async def get_knowledge_base(
    kb_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get knowledge base by ID
    """
    kb_service = KnowledgeBaseService(db)
    knowledge_base = await kb_service.get_by_id(kb_id)
    
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found"
        )
    
    # Check if user has access
    if not knowledge_base.is_public and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return knowledge_base


@router.put("/{kb_id}", response_model=KnowledgeBaseSchema)
async def update_knowledge_base(
    kb_id: str,
    kb_update: KnowledgeBaseUpdate,
    current_user: UserSchema = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update knowledge base (admin only)
    """
    kb_service = KnowledgeBaseService(db)
    knowledge_base = await kb_service.get_by_id(kb_id)
    
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found"
        )
    
    updated_kb = await kb_service.update(knowledge_base, kb_update)
    return updated_kb


@router.delete("/{kb_id}")
async def delete_knowledge_base(
    kb_id: str,
    current_user: UserSchema = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete knowledge base (admin only)
    """
    kb_service = KnowledgeBaseService(db)
    knowledge_base = await kb_service.get_by_id(kb_id)
    
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found"
        )
    
    await kb_service.delete(knowledge_base)
    return {"message": "Knowledge base deleted successfully"}


@router.post("/{kb_id}/search")
async def search_knowledge_base(
    kb_id: str,
    query: str,
    limit: int = 10,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Search within a specific knowledge base
    """
    kb_service = KnowledgeBaseService(db)
    knowledge_base = await kb_service.get_by_id(kb_id)
    
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found"
        )
    
    # Check if user has access
    if not knowledge_base.is_public and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        results = await kb_service.search_knowledge_base(
            kb_id=kb_id,
            query=query,
            limit=limit
        )
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching knowledge base: {str(e)}"
        )