"""
Singleton Embedding Service to avoid repeated initialization of OpenAIEmbeddings
"""
import logging
from typing import Optional, List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings
from .compatible_embeddings import CompatibleOpenAIEmbeddings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Singleton service for managing embeddings and text splitting"""
    
    _instance: Optional['EmbeddingService'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'EmbeddingService':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize()
            self._initialized = True
    
    def _initialize(self):
        """Initialize the embedding service components"""
        try:
            # Initialize Compatible OpenAI embeddings
            api_key = settings.EMBEDDING_API_KEY or settings.OPENAI_API_KEY
            base_url = settings.EMBEDDING_BASE_URL or "https://api.openai.com/v1"
            model = settings.EMBEDDING_MODEL or "text-embedding-ada-002"
            
            # Use the new CompatibleOpenAIEmbeddings class
            self.embeddings = CompatibleOpenAIEmbeddings(
                api_key=api_key,
                base_url=base_url,
                model=model
            )
            
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=300,
                chunk_overlap=100,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            logger.info("EmbeddingService initialized successfully with OpenAI embeddings")
            
        except Exception as e:
            logger.error(f"Failed to initialize EmbeddingService: {e}")
            raise
    
    def get_embeddings(self) -> CompatibleOpenAIEmbeddings:
        """Get the Compatible OpenAI embeddings instance"""
        return self.embeddings
    
    def get_text_splitter(self) -> RecursiveCharacterTextSplitter:
        """Get the text splitter instance"""
        return self.text_splitter
    
    @classmethod
    def get_instance(cls) -> 'EmbeddingService':
        """Get the singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# Global function to get the singleton instance
def get_embedding_service() -> EmbeddingService:
    """Get the singleton EmbeddingService instance"""
    return EmbeddingService.get_instance()