"""
Rerank service using LangChain and various rerank models
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor

from langchain_core.documents import Document as LangChainDocument

from app.core.config import settings

logger = logging.getLogger(__name__)


class RerankService:
    """Rerank service for improving retrieval results quality"""
    
    def __init__(self):
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize rerank model based on configuration"""
        if not settings.RERANK_ENABLED:
            logger.info("Rerank is disabled in configuration")
            return
        
        try:
            model_name = settings.RERANK_MODEL.strip()
            logger.info(f"Initializing rerank model: {model_name}")
            
            # Choose implementation based on model name
            if model_name.lower().startswith(("cross-encoder", "sentence-transformers")):
                from sentence_transformers import CrossEncoder
                self.model = CrossEncoder(model_name, device=settings.RERANK_DEVICE)
                logger.info("Sentence-transformers rerank model initialized successfully")
            else:
                # Prefer FlagEmbedding for BGE rerankers
                try:
                    from FlagEmbedding import FlagReranker
                    self.model = FlagReranker(
                        model_name,
                        use_fp16=True if settings.RERANK_DEVICE == "cuda" else False,
                        device=settings.RERANK_DEVICE
                    )
                    logger.info("FlagEmbedding rerank model initialized successfully")
                except Exception as e:
                    logger.warning(f"FlagEmbedding init failed ({e}); falling back to CrossEncoder")
                    from sentence_transformers import CrossEncoder
                    # Fallback to a lightweight cross-encoder if provided model is incompatible
                    fallback_model = model_name if model_name.lower().startswith("cross-encoder") else "cross-encoder/ms-marco-MiniLM-L-6-v2"
                    try:
                        self.model = CrossEncoder(fallback_model, device=settings.RERANK_DEVICE)
                        logger.info("Sentence-transformers rerank model initialized successfully (fallback)")
                    except Exception as e2:
                        logger.error(f"Failed to initialize any rerank model: {e2}")
                        self.model = None
        except Exception as e:
            logger.error(f"Unexpected error during rerank model initialization: {e}")
            self.model = None
    
    def _compute_rerank_scores(self, query: str, documents: List[str]) -> List[float]:
        """Compute rerank scores for documents"""
        if not self.model:
            # Return original order scores if model is not available
            return [1.0 - i * 0.1 for i in range(len(documents))]
        
        try:
            # Prepare query-document pairs
            pairs = [[query, doc] for doc in documents]
            
            # Compute scores based on model type
            if hasattr(self.model, 'compute_score'):
                # FlagReranker
                scores = self.model.compute_score(pairs, normalize=True)
            else:
                # CrossEncoder
                scores = self.model.predict(pairs)
            
            # Ensure scores is a list
            if not isinstance(scores, list):
                scores = scores.tolist()
            
            return scores
            
        except Exception as e:
            logger.error(f"Error computing rerank scores: {e}")
            # Return fallback scores
            return [1.0 - i * 0.1 for i in range(len(documents))]
    
    async def rerank_documents(
        self,
        query: str,
        documents: List[LangChainDocument],
        sources: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> Tuple[List[LangChainDocument], List[Dict[str, Any]]]:
        """
        Rerank documents based on query relevance
        
        Args:
            query: Search query
            documents: List of LangChain documents
            sources: List of source metadata
            top_k: Number of top results to return (defaults to RERANK_FINAL_K)
        
        Returns:
            Tuple of (reranked_documents, reranked_sources)
        """
        if not settings.RERANK_ENABLED or not self.model or not documents:
            return documents, sources
        
        if top_k is None:
            top_k = settings.RERANK_FINAL_K
        
        try:
            # Limit candidates to RERANK_TOP_K for efficiency
            max_candidates = min(len(documents), settings.RERANK_TOP_K)
            candidate_docs = documents[:max_candidates]
            candidate_sources = sources[:max_candidates]
            
            # Extract document texts for reranking
            doc_texts = [doc.page_content for doc in candidate_docs]
            
            # Compute rerank scores in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            rerank_scores = await loop.run_in_executor(
                self.executor,
                self._compute_rerank_scores,
                query,
                doc_texts
            )
            
            # Combine documents with their rerank scores
            doc_score_pairs = []
            for i, (doc, source, rerank_score) in enumerate(zip(candidate_docs, candidate_sources, rerank_scores)):
                # Store original scores for comparison
                original_score = source.get('combined_score', 0.0)
                
                # Update source with rerank information
                updated_source = source.copy()
                updated_source.update({
                    'rerank_score': float(rerank_score),
                    'original_score': float(original_score),
                    'rerank_enabled': True,
                    'rerank_model': settings.RERANK_MODEL
                })
                
                doc_score_pairs.append((doc, updated_source, float(rerank_score)))
            
            # Sort by rerank score (descending)
            doc_score_pairs.sort(key=lambda x: x[2], reverse=True)
            
            # Extract top_k results
            top_pairs = doc_score_pairs[:top_k]
            reranked_docs = [pair[0] for pair in top_pairs]
            reranked_sources = [pair[1] for pair in top_pairs]
            
            logger.info(f"Reranked {len(candidate_docs)} documents, returning top {len(reranked_docs)}")
            
            return reranked_docs, reranked_sources
            
        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            # Return original results on error
            return documents[:top_k], sources[:top_k]
    
    def is_enabled(self) -> bool:
        """Check if rerank is enabled and model is available"""
        return settings.RERANK_ENABLED and self.model is not None


# Global rerank service instance
_rerank_service = None


def get_rerank_service() -> RerankService:
    """Get global rerank service instance"""
    global _rerank_service
    if _rerank_service is None:
        _rerank_service = RerankService()
    return _rerank_service