"""
Knowledge Assistant endpoints for document processing and Q&A
"""
from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json
import asyncio

from app.core.database import get_db
from app.schemas.document import Document as DocumentSchema
from app.schemas.user import User as UserSchema
from app.services.enhanced_document_service import EnhancedDocumentService
from app.services.lightweight_document_service import LightweightDocumentService
from app.services.rag_service import RAGService
from app.core.config import settings
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/upload", response_model=DocumentSchema)
async def upload_knowledge_document(
    file: UploadFile = File(...),
    knowledge_base_id: str = Form(None),
    category: str = Form("knowledge"),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Upload a document for knowledge base processing with automatic chunking and vectorization
    """
    document_service = EnhancedDocumentService(db)
    
    try:
        # Upload and process document with LangChain
        document = await document_service.upload_and_process_document(
            file=file,
            user_id=current_user.id,
            knowledge_base_id=knowledge_base_id,
            category=category
        )
        
        return document
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )


@router.post("/search")
async def search_knowledge(
    query: str = Form(...),
    knowledge_base_id: str = Form(None),
    limit: int = Form(10),
    similarity_threshold: float = Form(0.7),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Search knowledge base using semantic similarity via RAG service
    """
    try:
        # Initialize RAG service
        rag_service = RAGService(db)
        
        # Convert knowledge_base_id from string to UUID if provided
        kb_id = None
        if knowledge_base_id:
            try:
                from uuid import UUID
                kb_id = UUID(knowledge_base_id)
            except (ValueError, TypeError):
                pass  # Use None if invalid UUID
        
        # Use RAG service for document search
        results = await rag_service.search_documents(
            query=query,
            user_id=current_user.id,
            knowledge_base_id=kb_id,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
        
        return {
            "query": query,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching knowledge: {str(e)}"
        )


@router.post("/ask")
async def ask_knowledge_assistant(
    question: str = Form(...),
    knowledge_base_id: str = Form(None),
    context_limit: int = Form(5),
    conversation_history: str = Form("[]"),  # JSON string of conversation history
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Ask a question to the knowledge assistant using RAG workflow with streaming response
    """
    try:
        # Initialize RAG service
        rag_service = RAGService(db)
        
        # Convert knowledge_base_id from string to UUID if provided
        kb_id = None
        if knowledge_base_id:
            try:
                from uuid import UUID
                kb_id = UUID(knowledge_base_id)
            except (ValueError, TypeError):
                pass  # Use None if invalid UUID
        
        # Parse conversation history
        try:
            conv_history = json.loads(conversation_history) if conversation_history else []
        except json.JSONDecodeError:
            conv_history = []
        
        # Use RAG service to generate answer with streaming
        async def generate_stream():
            try:
                # Use the new streaming method from RAG service
                async for chunk in rag_service.ask_question_stream(
                    question=question,
                    user_id=current_user.id,
                    knowledge_base_id=kb_id,
                    conversation_history=conv_history,
                    context_limit=context_limit
                ):
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                    
            except Exception as e:
                error_data = {
                    "type": "error",
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating answer: {str(e)}"
        )


@router.get("/documents")
async def get_knowledge_documents(
    knowledge_base_id: str = None,
    skip: int = 0,
    limit: int = 20,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get documents in knowledge base - optimized for performance
    """
    # Use lightweight service for document listing (no LLM initialization needed)
    document_service = LightweightDocumentService(db)
    
    try:
        # Convert knowledge_base_id from string to UUID if provided
        kb_id = None
        if knowledge_base_id:
            try:
                from uuid import UUID
                kb_id = UUID(knowledge_base_id)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid knowledge_base_id format"
                )
        
        documents = await document_service.get_user_documents(
            user_id=current_user.id,
            knowledge_base_id=kb_id,
            skip=skip,
            limit=limit
        )
        
        # Convert SQLAlchemy models to dictionaries for serialization
        documents_data = []
        for doc in documents:
            doc_dict = {
                "id": str(doc.id),
                "filename": doc.filename,
                "original_filename": doc.original_filename,
                "file_path": doc.file_path,
                "file_size": doc.file_size,
                "file_hash": doc.file_hash,
                "mime_type": doc.mime_type,
                "extracted_content": doc.extracted_content,
                "summary": doc.summary,
                "category": doc.category,
                "tags": doc.tags or [],
                "knowledge_base_id": str(doc.knowledge_base_id) if doc.knowledge_base_id else None,
                "user_id": str(doc.user_id),
                "meta_data": doc.meta_data or {},
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
            }
            documents_data.append(doc_dict)
        
        return {
            "documents": documents_data,
            "total": len(documents_data)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving documents: {str(e)}"
        )


@router.delete("/documents/{document_id}")
async def delete_knowledge_document(
    document_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete a knowledge document and its chunks
    """
    # Use enhanced service for deletion as it may need to clean up vectors
    document_service = EnhancedDocumentService(db)
    
    try:
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
        
        await document_service.delete_document(document_id)
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )