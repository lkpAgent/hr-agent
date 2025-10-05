"""
Document management endpoints
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.document import Document as DocumentSchema, DocumentCreate
from app.schemas.user import User as UserSchema
from app.services.enhanced_document_service import EnhancedDocumentService
from app.services.lightweight_document_service import LightweightDocumentService
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/", response_model=List[DocumentSchema])
async def get_documents(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get documents - optimized for performance
    """
    # Use lightweight service for document listing (no LLM initialization needed)
    document_service = LightweightDocumentService(db)
    documents = await document_service.get_user_documents(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        category=category
    )
    return documents


@router.post("/upload", response_model=DocumentSchema)
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form(None),
    tags: List[str] = Form(None),
    knowledge_base_id: str = Form(None),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Upload a new document
    """
    document_service = EnhancedDocumentService(db)
    
    try:
        document = await document_service.upload_document(
            file=file,
            user_id=current_user.id,
            category=category,
            tags=tags or [],
            knowledge_base_id=knowledge_base_id
        )
        return document
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentSchema)
async def get_document(
    document_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get document by ID - optimized for performance
    """
    # Use lightweight service for document retrieval (no LLM initialization needed)
    document_service = LightweightDocumentService(db)
    document = await document_service.get_by_id(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check permissions
    if document.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return document


@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get document chunks for preview
    """
    document_service = EnhancedDocumentService(db)
    
    try:
        chunks = await document_service.get_document_chunks(document_id, current_user.id)
        return {"chunks": chunks}
        
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        elif "Permission denied" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting document chunks: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete document
    """
    document_service = EnhancedDocumentService(db)
    document = await document_service.get_by_id(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check permissions
    if document.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    await document_service.delete(document)
    return {"message": "Document deleted successfully"}


@router.post("/search")
async def search_documents(
    query: str,
    limit: int = 10,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Search documents using vector similarity
    """
    document_service = EnhancedDocumentService(db)
    
    try:
        results = await document_service.search_documents(
            query=query,
            user_id=current_user.id,
            limit=limit
        )
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching documents: {str(e)}"
        )