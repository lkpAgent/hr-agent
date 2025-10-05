"""
Enhanced document service with LangChain integration for document processing and vectorization
"""
import logging
import os
import hashlib
from typing import List, Optional, Dict, Any, BinaryIO
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc, func
from sqlalchemy.orm import selectinload

# LangChain imports
from langchain_core.documents import Document as LangChainDocument
from langchain_postgres import PGVector

# Document processing imports
import PyPDF2
from docx import Document as DocxDocument
import tempfile

from app.models.document import Document, DocumentChunk
from app.models.knowledge_base import KnowledgeBase
from app.services.llm_service import LLMService
from app.services.embedding_service import get_embedding_service
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.core.config import settings

logger = logging.getLogger(__name__)


class EnhancedDocumentService:
    """Enhanced service for managing documents with LangChain integration"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_service = LLMService()
        
        # Use shared embedding service to avoid repeated initialization
        self.embedding_service = get_embedding_service()
        self.embeddings = self.embedding_service.get_embeddings()
        self.text_splitter = self.embedding_service.get_text_splitter()
        
        # Database connection string for PGVector (use psycopg2 for sync connection)
        self.connection_string = settings.DATABASE_URL
        
        logger.info("Enhanced document service initialized with shared embedding service")

    async def upload_document(
        self,
        file,  # UploadFile object
        user_id: UUID,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        knowledge_base_id: Optional[str] = None
    ) -> Document:
        """Upload and process a document"""
        # Convert knowledge_base_id from string to UUID if provided
        kb_id = None
        if knowledge_base_id:
            try:
                kb_id = UUID(knowledge_base_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid knowledge_base_id format: {knowledge_base_id}")
                kb_id = None
        
        return await self.upload_and_process_document(
            file=file.file,
            filename=file.filename,
            user_id=user_id,
            knowledge_base_id=kb_id,
            category=category,
            tags=tags
        )

    async def upload_and_process_document(
        self,
        file: BinaryIO,
        filename: str,
        user_id: UUID,
        knowledge_base_id: Optional[UUID] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Document:
        """Upload and process document with full text extraction and vectorization"""
        try:
            # Read file content
            file_content = file.read()
            file.seek(0)  # Reset file pointer
            
            # Generate file hash
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Check if document already exists
            existing_doc = await self._get_document_by_hash(file_hash, user_id)
            if existing_doc:
                logger.info(f"Document with hash {file_hash} already exists")
                return existing_doc
            
            # Determine MIME type
            mime_type = self._get_mime_type(filename)
            
            # Save file temporarily for processing
            temp_file_path = await self._save_temp_file(file_content, filename)
            
            try:
                # Extract text content
                extracted_content = await self._extract_text_content(temp_file_path, mime_type)
                
                # Generate summary
                summary = await self.llm_service.summarize_text(extracted_content) if extracted_content else None
                
                # Generate embedding for the document
                # document_embedding = await self.embeddings.aembed_query(extracted_content) if extracted_content else None
                
                # Save file permanently
                file_path = await self._save_file(file_content, filename, user_id)
                
                # Create document record
                document = Document(
                    filename=filename,
                    original_filename=filename,
                    file_path=file_path,
                    file_size=len(file_content),
                    file_hash=file_hash,
                    mime_type=mime_type,
                    extracted_content=extracted_content,
                    summary=summary,
                    embedding=None,  # We use PGVector for embeddings now
                    category=category,
                    tags=tags,
                    user_id=user_id,
                    knowledge_base_id=knowledge_base_id
                )
                
                self.db.add(document)
                await self.db.commit()
                await self.db.refresh(document)
                
                # Create document chunks using PGVector
                if extracted_content:
                    await self._create_document_chunks_with_pgvector(document, extracted_content)
                
                logger.info(f"Document uploaded and processed successfully: {document.id}")
                return document
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            await self.db.rollback()
            raise

    async def _create_document_chunks_with_pgvector(self, document: Document, content: str):
        """Create document chunks using PGVector for storage"""
        try:
            # Split text into chunks
            text_chunks = self.text_splitter.split_text(content)
            
            # Create LangChain documents
            langchain_docs = []
            for i, chunk_text in enumerate(text_chunks):
                doc = LangChainDocument(
                    page_content=chunk_text,
                    metadata={
                        "document_id": str(document.id),
                        "chunk_index": i,
                        "chunk_size": len(chunk_text),
                        "filename": document.filename,
                        "category": document.category,
                        "knowledge_base_id": str(document.knowledge_base_id)
                    }
                )
                langchain_docs.append(doc)
            
            if langchain_docs:
                # Use PGVector to store documents with embeddings
                collection_name = f"document_chunks_{document.user_id}".replace("-", "_")
                
                # Connect to existing collection or create new one
                vector_store = PGVector(
                    connection=self.connection_string,
                    embeddings=self.embeddings,
                    collection_name=collection_name,
                    use_jsonb=True
                )
                
                # Add documents to vector store (synchronous operation)
                try:
                    vector_store.add_documents(langchain_docs)
                    logger.info(f"Successfully added {len(langchain_docs)} documents to PGVector collection: {collection_name}")
                except Exception as e:
                    logger.error(f"Error adding documents to PGVector: {e}")
                    raise
                
                # Create records in our DocumentChunk table for consistency (optional)
                for i, chunk_text in enumerate(text_chunks):
                    chunk = DocumentChunk(
                        content=chunk_text,
                        chunk_index=i,
                        chunk_size=len(chunk_text),
                        embedding=None,  # Use None for Vector fields when using PGVector
                        document_id=document.id,
                        meta_data={
                            "filename": document.filename,
                            "category": document.category
                        }
                    )
                    self.db.add(chunk)
                
                await self.db.commit()
                logger.info(f"Created {len(text_chunks)} chunks for document {document.id}")
                
        except Exception as e:
            logger.error(f"Error creating document chunks: {e}")
            await self.db.rollback()
            raise

    async def search_documents(
        self,
        query: str,
        user_id: UUID,
        limit: int = 10,
        knowledge_base_id: Optional[UUID] = None,
        category: Optional[str] = None,
        similarity_threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Search documents (wrapper for semantic_search)"""
        return await self.semantic_search(
            query=query,
            user_id=user_id,
            limit=limit,
            knowledge_base_id=knowledge_base_id,
            category=category,
            similarity_threshold=similarity_threshold
        )

    async def semantic_search(
        self,
        query: str,
        user_id: UUID,
        limit: int = 10,
        knowledge_base_id: Optional[UUID] = None,
        category: Optional[str] = None,
        similarity_threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using PGVector"""
        try:
            collection_name = f"document_chunks_{user_id}".replace("-", "_")
            
            # Connect to vector store
            vector_store = PGVector(
                connection=self.connection_string,
                embeddings=self.embeddings,
                collection_name=collection_name,
                use_jsonb=True
            )
            
            # Build filter conditions
            filter_conditions = {}
            if knowledge_base_id:
                filter_conditions["knowledge_base_id"] = str(knowledge_base_id)
            if category:
                filter_conditions["category"] = category
            
            # Perform similarity search
            results = vector_store.similarity_search_with_score(
                query=query,
                k=limit,
                filter=filter_conditions if filter_conditions else None
            )
            
            # Format results
            search_results = []
            for doc, score in results:
                if score <= similarity_threshold:
                    search_results.append({
                        "document_id": doc.metadata.get("document_id"),
                        "filename": doc.metadata.get("filename"),
                        "content": doc.page_content,
                        "chunk_index": doc.metadata.get("chunk_index"),
                        "category": doc.metadata.get("category"),
                        "similarity": float(score),
                        "metadata": doc.metadata
                    })
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            # Fallback to text search
            return await self._fallback_text_search(query, user_id, limit, knowledge_base_id, category)

    async def _fallback_text_search(
        self,
        query: str,
        user_id: UUID,
        limit: int,
        knowledge_base_id: Optional[UUID] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fallback text search when vector search fails"""
        try:
            base_query = select(Document).where(Document.user_id == user_id)
            
            if knowledge_base_id:
                base_query = base_query.where(Document.knowledge_base_id == knowledge_base_id)
            
            if category:
                base_query = base_query.where(Document.category == category)
            
            # Simple text search
            text_query = base_query.where(
                Document.extracted_content.ilike(f"%{query}%")
            ).limit(limit)
            
            result = await self.db.execute(text_query)
            documents = result.scalars().all()
            
            # Format results
            search_results = []
            for doc in documents:
                search_results.append({
                    "document_id": str(doc.id),
                    "filename": doc.filename,
                    "content": doc.extracted_content[:500] if doc.extracted_content else "",
                    "summary": doc.summary,
                    "category": doc.category,
                    "similarity": 0.5,  # Default similarity for text search
                    "created_at": doc.created_at.isoformat()
                })
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error in fallback text search: {e}")
            return []

    async def get_user_documents(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        knowledge_base_id: Optional[UUID] = None
    ) -> List[Document]:
        """Get user documents with optional filtering"""
        try:
            query = select(Document).where(Document.user_id == user_id)
            
            if category:
                query = query.where(Document.category == category)
            
            if knowledge_base_id:
                query = query.where(Document.knowledge_base_id == knowledge_base_id)
            
            query = query.offset(skip).limit(limit).order_by(desc(Document.created_at))
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting user documents: {e}")
            raise

    async def get_by_id(self, document_id: str) -> Optional[Document]:
        """Get document by ID"""
        try:
            query = select(Document).where(Document.id == document_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting document by ID: {e}")
            return None

    async def get_document_chunks(self, document_id: str, user_id: UUID) -> List[Dict[str, Any]]:
        """Get document chunks for preview"""
        try:
            # First check if document exists and user has permission
            document = await self.get_by_id(document_id)
            if not document:
                raise ValueError("Document not found")
            
            if document.user_id != user_id:
                raise ValueError("Permission denied")
            
            # Get chunks from database
            query = select(DocumentChunk).where(
                DocumentChunk.document_id == document_id
            ).order_by(DocumentChunk.chunk_index)
            
            result = await self.db.execute(query)
            chunks = result.scalars().all()
            
            # Format chunks for response
            formatted_chunks = []
            for chunk in chunks:
                formatted_chunks.append({
                    "id": str(chunk.id),
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "chunk_size": chunk.chunk_size,
                    "metadata": chunk.meta_data
                })
            
            return formatted_chunks
            
        except Exception as e:
            logger.error(f"Error getting document chunks: {e}")
            raise

    async def delete(self, document: Document) -> None:
        """Delete a document and its chunks"""
        try:
            # Delete document chunks first
            await self.db.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
            )
            
            # Delete the document
            await self.db.delete(document)
            await self.db.commit()
            
            # Clean up file if it exists
            if document.file_path and os.path.exists(document.file_path):
                os.unlink(document.file_path)
                
            logger.info(f"Deleted document {document.id}")
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            await self.db.rollback()
            raise

    async def _get_document_by_hash(
        self,
        file_hash: str,
        user_id: UUID
    ) -> Optional[Document]:
        """Get document by file hash"""
        query = select(Document).where(
            Document.file_hash == file_hash,
            Document.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def _get_mime_type(self, filename: str) -> str:
        """Determine MIME type from filename"""
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        mime_types = {
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain',
            'md': 'text/markdown',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xls': 'application/vnd.ms-excel'
        }
        return mime_types.get(extension, 'application/octet-stream')

    async def _save_temp_file(self, content: bytes, filename: str) -> str:
        """Save file temporarily for processing"""
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"temp_{filename}")
        
        with open(temp_file_path, 'wb') as f:
            f.write(content)
        
        return temp_file_path

    async def _save_file(self, content: bytes, filename: str, user_id: UUID) -> str:
        """Save file permanently"""
        # Create user-specific upload directory
        upload_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_path = os.path.join(upload_dir, filename)
        counter = 1
        base_name, extension = os.path.splitext(filename)
        
        while os.path.exists(file_path):
            new_filename = f"{base_name}_{counter}{extension}"
            file_path = os.path.join(upload_dir, new_filename)
            counter += 1
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return file_path

    async def _extract_text_content(self, file_path: str, mime_type: str) -> str:
        """Extract text content from file"""
        try:
            if mime_type == 'text/plain' or mime_type == 'text/markdown':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif mime_type == 'application/pdf':
                text = ""
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                return text.strip()
            
            elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                if mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                    doc = DocxDocument(file_path)
                    text = ""
                    for paragraph in doc.paragraphs:
                        text += paragraph.text + "\n"
                    return text.strip()
                else:
                    # For .doc files, we'd need python-docx2txt or similar
                    logger.warning(f"Unsupported document format: {mime_type}")
                    return ""
            
            else:
                logger.warning(f"Unsupported file type: {mime_type}")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""