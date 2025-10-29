"""
RAG (Retrieval Augmented Generation) service using LangChain
"""
import logging
import re
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# LangChain imports
from langchain_core.documents import Document as LangChainDocument
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_postgres import PGVector
from langchain_openai import ChatOpenAI

from app.services.embedding_service import get_embedding_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """RAG service implementing LangChain standard workflow"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Initialize embedding service
        self.embedding_service = get_embedding_service()
        self.embeddings = self.embedding_service.get_embeddings()
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            temperature=0.7,
            max_tokens=2000
        )
        
        # Database connection string for PGVector
        self.connection_string = settings.DATABASE_URL
        
        logger.info("RAG service initialized with LangChain components")

    async def _tsvector_search(
        self,
        collection_name: str,
        query: str,
        k: int = 5,
        knowledge_base_id: Optional[UUID] = None
    ) -> List[tuple]:
        """
        PostgreSQL全文检索（tsvector）基于 langchain_pg_embedding.document。
        - 集合名严格过滤：cmetadata->>'collection_name'
        - 查询重写为 OR 前缀 tsquery（Elasticsearch match 类似：任一词命中即返回）
        - 对中文/英中混合词保留 ILIKE 后备，提高召回
        返回 (LangChainDocument, score) 列表，与向量检索输出格式一致。
        """
        try:
            # 1) 查询重写：提取英文/数字/中文词元，移除常见问句停用词，构造 OR 前缀 tsquery
            stop_words = {"有哪些", "什么", "如何", "怎么", "请问", "的", "和", "与"}
            terms = re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]+", query)
            terms = [t.lower() for t in terms if t not in stop_words and len(t) >= 2]
            tsquery_or = " | ".join(f"{t}:*" for t in terms) if terms else None

            # 2) 构建 SQL：优先使用 to_tsquery(simple, :tsq) 的 OR 匹配；保留 ILIKE 兜底
            base_sql = (
                "SELECT id, document, cmetadata, "
                "ts_rank_cd(to_tsvector('simple', document), to_tsquery('simple', :tsq)) AS rank "
                "FROM langchain_pg_embedding "
                "WHERE cmetadata->>'collection_name' = :collection_name "
                "AND ("
                "     ( :tsq IS NOT NULL AND to_tsvector('simple', document) @@ to_tsquery('simple', :tsq) ) "
                "     OR document ILIKE '%' || :q || '%'"
                ") "
            )
            params = {"q": query, "tsq": tsquery_or, "collection_name": collection_name, "limit": k}
            
            if knowledge_base_id:
                base_sql += "AND cmetadata->>'knowledge_base_id' = :kb_id "
                params["kb_id"] = str(knowledge_base_id)
            
            base_sql += "ORDER BY rank DESC LIMIT :limit"

            res2 = await self.db.execute(text(base_sql), params)
            rows = res2.fetchall()
            results: List[tuple] = []
            for r in rows:
                doc_text = r[1]
                metadata = r[2] or {}
                page_content = doc_text
                lc_doc = LangChainDocument(page_content=page_content, metadata=metadata)
                results.append((lc_doc, float(r[3]) if r[3] is not None else 0.0))
            return results
        except Exception as e:
            logger.warning(f"tsvector search error: {e}")
            return []

    def _merge_docs_with_scores(
        self,
        content_results: List[tuple],
        text_results: List[tuple],
        top_k: int = 5
    ) -> (List[LangChainDocument], List[Dict[str, Any]]):
        """Merge vector content results with PostgreSQL tsvector results.
        Weighted combination and return top_k docs plus source metadata."""
        try:
            merged_map: Dict[tuple, Dict[str, Any]] = {}

            for doc, score in content_results:
                key = (doc.metadata.get("document_id"), doc.metadata.get("chunk_index"))
                merged_map[key] = merged_map.get(key, {"doc": doc, "content_score": 0.0})
                merged_map[key]["doc"] = doc
                merged_map[key]["content_score"] = float(score)

            # Integrate tsvector text search results
            for doc, score in text_results:
                key = (doc.metadata.get("document_id"), doc.metadata.get("chunk_index"))
                entry = merged_map.get(key, {"doc": doc, "content_score": 0.0})
                entry["doc"] = entry.get("doc") or doc
                entry["text_score"] = float(score)
                merged_map[key] = entry

            # Combine scores: prioritize content similarity, then keyword match
            combined_list: List[tuple] = []
            for key, entry in merged_map.items():
                content_score = float(entry.get("content_score", 0.0))
                text_score = float(entry.get("text_score", 0.0))
                # Weighted combination: content (0.7), text (0.3)
                combined_score = 0.7 * content_score + 0.3 * text_score
                combined_list.append((entry["doc"], combined_score, entry))

            # Sort by combined_score descending (higher relevance first)
            combined_list.sort(key=lambda x: x[1], reverse=True)

            # Build outputs
            top = combined_list[:top_k]
            docs: List[LangChainDocument] = []
            sources: List[Dict[str, Any]] = []
            for doc, combined_score, entry in top:
                final_page_content = doc.page_content
                final_doc = LangChainDocument(page_content=final_page_content, metadata=doc.metadata)
                docs.append(final_doc)
                sources.append({
                    "document_id": doc.metadata.get("document_id"),
                    "document_title": doc.metadata.get("filename", "Unknown"),
                    "chunk_id": doc.metadata.get("chunk_id"),
                    "chunk_index": doc.metadata.get("chunk_index", 0),
                    "content": final_page_content,
                    "combined_score": float(combined_score),
                    "content_score": float(entry.get("content_score", 0.0)),
                    "text_score": float(entry.get("text_score", 0.0)),
                    "metadata": doc.metadata
                })
            return docs, sources
        except Exception as e:
            logger.warning(f"Error merging multi-route results: {e}")
            # Fallback: return content_results only
            docs = [doc for doc, _ in content_results[:top_k]]
            sources = []
            for doc, score in content_results[:top_k]:
                sources.append({
                    "document_id": doc.metadata.get("document_id"),
                    "document_title": doc.metadata.get("filename", "Unknown"),
                    "chunk_id": doc.metadata.get("chunk_id"),
                    "chunk_index": doc.metadata.get("chunk_index", 0),
                    "content": doc.page_content,
                    "combined_score": float(score),
                    "content_score": float(score),
                    "text_score": 0.0,
                    "metadata": doc.metadata
                })
            return docs, sources
    
    def _create_rag_chain(self, retriever, conversation_history: List[Dict[str, str]]):
        """Create RAG chain with conversation history."""
        
        # Create prompt template
        system_prompt = """你是一个智能助手，基于提供的上下文信息回答用户问题。

上下文信息：
{context}

请根据上下文信息回答用户的问题。如果上下文信息不足以回答问题，请诚实地说明。
保持回答准确、有用且简洁。"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        # Create chain
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        rag_chain = (
            {
                "context": retriever | format_docs,
                "question": RunnablePassthrough(),
                "chat_history": lambda x: conversation_history
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return rag_chain
    
    def _create_rag_chain_with_docs(self, docs: List[LangChainDocument], conversation_history: List[Dict[str, str]]):
        """Create RAG chain with pre-retrieved documents."""
        
        # Create prompt template
        system_prompt = """你是一个智能助手，基于提供的上下文信息回答用户问题。

上下文信息：
{context}

请根据上下文信息回答用户的问题。如果上下文信息不足以回答问题，请诚实地说明。
保持回答准确、有用且简洁。"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        # Format documents
        def format_docs(docs_list):
            return "\n\n".join(doc.page_content for doc in docs_list)
        
        # Create chain with pre-retrieved documents
        rag_chain = (
            {
                "context": lambda x: format_docs(docs),
                "question": RunnablePassthrough(),
                "chat_history": lambda x: conversation_history
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return rag_chain

    def _should_use_knowledge_base(self, question: str) -> bool:
        """Decide whether the user's question should use knowledge base retrieval.
        Returns True if KB should be used, otherwise False.
        """
        try:


            # LLM-based classification with explicit instruction and examples
            classification_prompt = (
                "你是一个分类器。判断该问题是否需要基于知识库内容回答还是由大模型自主回答。\n"
                "只有用户在明显是闲聊的内容才输出GENERAL。\n"
                "其他情况都输出KB\n"
                "示例：\n"
                "问：讲个笑话\n答：GENERAL\n"
                "问：你好\n答：GENERAL\n"
                "问：你是谁\n答：GENERAL\n"
                "问：作首诗\n答：GENERAL\n"
                "而其他情况或者判断不准的时候，都输出KB\n"
                f"问：{question}\n答："
            )
            # Use a deterministic classifier LLM
            from langchain_openai import ChatOpenAI
            classifier_llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL,
                temperature=0,
                max_tokens=10
            )
            resp = classifier_llm.invoke(classification_prompt)
            content = getattr(resp, "content", str(resp))
            return "KB" in (content or "").upper()
        except Exception as e:
            logger.warning(f"KB intent detection failed, defaulting to KB: {e}")
            return True

    def _create_general_chat_chain(self, conversation_history: List[Dict[str, str]]):
        """General chat chain without KB context."""
        system_prompt = (
            "你是一个智能助手。直接根据用户问题进行回答，不使用任何知识库上下文。"
            "保持回答准确、简洁、有帮助。"
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        chain = (
            {
                "question": RunnablePassthrough(),
                "chat_history": lambda x: conversation_history
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
        return chain
        
    async def ask_question_stream(
        self,
        question: str,
        user_id: UUID,
        knowledge_base_id: Optional[UUID] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context_limit: int = 5
    ):
        """
        Ask a question using RAG workflow with streaming response
        
        Args:
            question: User question
            user_id: User ID for document filtering
            knowledge_base_id: Optional knowledge base ID for filtering
            conversation_history: Previous conversation messages
            context_limit: Maximum number of context documents to retrieve
            
        Yields:
            Dict containing streaming response data
        """
        try:
            conversation_history = conversation_history or []
            
            # Intent detection first
            use_kb = self._should_use_knowledge_base(question)
            print('use_kb=======', use_kb)
            # If a specific knowledge base is provided, always use KB retrieval
            # if knowledge_base_id:
            #     use_kb = True
            
            logger.info(f"ask_question_stream: use_kb={use_kb}, knowledge_base_id={knowledge_base_id}, user_id={user_id}")
            
            if not use_kb:
                # Stream general LLM answer without KB retrieval
                yield {
                    "type": "start",
                    "question": question,
                    "sources": [],
                    "context_used": False,
                    "num_sources": 0
                }
                general_chain = self._create_general_chat_chain(conversation_history)
                async for chunk in general_chain.astream(question):
                    if chunk:
                        yield {"type": "chunk", "content": chunk}
                yield {"type": "end", "complete": True, "sources": [], "num_sources": 0}
                return
            
            # Create collection name for user's documents (chunks only)
            collection_name = f"document_chunks_{user_id}".replace("-", "_")
            
            # Connect to vector store
            vector_store = PGVector(
                connection=self.connection_string,
                embeddings=self.embeddings,
                collection_name=collection_name,
                use_jsonb=True
            )
            # Keywords store removed; keep only chunks vector store
            
            # Build filter conditions
            filter_conditions = {}
            if knowledge_base_id:
                filter_conditions["knowledge_base_id"] = str(knowledge_base_id)
            
            # Multi-route retrieval: content (vector) + text (tsvector)
            # vector route
            content_results = vector_store.similarity_search_with_relevance_scores(
                question, k=context_limit, filter=filter_conditions if filter_conditions else None
            )

            # Second route: PostgreSQL tsvector full-text search on chunk collection
            text_results = await self._tsvector_search(collection_name, question, k=context_limit, knowledge_base_id=knowledge_base_id)

            # Merge and pick final docs and sources
            relevant_docs, sources = self._merge_docs_with_scores(content_results, text_results, top_k=context_limit)
            
            # Yield initial data with sources
            yield {
                "type": "start",
                "question": question,
                "sources": sources,
                "context_used": len(relevant_docs) > 0,
                "num_sources": len(sources)
            }
            
            # Create RAG chain with pre-retrieved documents (no additional retrieval)
            rag_chain = self._create_rag_chain_with_docs(relevant_docs, conversation_history)
            
            # Stream the response from LLM
            async for chunk in rag_chain.astream(question):
                if chunk:  # Only yield non-empty chunks
                    yield {
                        "type": "chunk",
                        "content": chunk
                    }
            
            # Yield completion signal with sources for frontend display
            yield {
                "type": "end",
                "complete": True,
                "sources": sources,
                "num_sources": len(sources)
            }
            
        except Exception as e:
            logger.error(f"Error in streaming RAG question answering: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }
    
    async def ask_question(
        self,
        question: str,
        user_id: UUID,
        knowledge_base_id: Optional[UUID] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Ask a question using RAG workflow
        
        Args:
            question: User's question
            user_id: User ID for document filtering
            knowledge_base_id: Optional knowledge base ID for filtering
            conversation_history: Previous conversation messages
            context_limit: Maximum number of context documents to retrieve
            
        Returns:
            Dictionary containing answer, sources, and metadata
        """
        try:
            # Prepare conversation history
            if conversation_history is None:
                conversation_history = []
            
            # Intent detection first
            use_kb = self._should_use_knowledge_base(question)
            # If a specific knowledge base is provided, always use KB retrieval
            if knowledge_base_id:
                use_kb = True
            
            logger.info(f"ask_question: use_kb={use_kb}, knowledge_base_id={knowledge_base_id}, user_id={user_id}")
            
            if not use_kb:
                # General chat path without KB
                chain = self._create_general_chat_chain(conversation_history)
                answer = chain.invoke(question)
                return {
                    "question": question,
                    "answer": answer,
                    "sources": [],
                    "context_used": False,
                    "num_sources": 0
                }
            
            # Create collection names for user's documents (chunks only)
            collection_name = f"document_chunks_{user_id}".replace("-", "_")
            
            # Connect to vector store
            vector_store = PGVector(
                connection=self.connection_string,
                embeddings=self.embeddings,
                collection_name=collection_name,
                use_jsonb=True
            )
            # Keywords store removed; keep only chunks vector store
            
            # Build filter conditions
            filter_conditions = {}
            if knowledge_base_id:
                filter_conditions["knowledge_base_id"] = str(knowledge_base_id)
            
            # Multi-route retrieval: content (vector) + text (tsvector)
            content_results = vector_store.similarity_search_with_relevance_scores(
                question, k=context_limit, filter=filter_conditions if filter_conditions else None
            )

            # Third route: PostgreSQL tsvector full-text search on chunk collection
            text_results = await self._tsvector_search(collection_name, question, k=context_limit, knowledge_base_id=knowledge_base_id)

            relevant_docs, sources = self._merge_docs_with_scores(content_results, text_results, top_k=context_limit)
            
            # Create RAG chain using pre-fetched docs
            rag_chain = self._create_rag_chain_with_docs(relevant_docs, conversation_history)
            
            # Generate answer using RAG chain
            answer = rag_chain.invoke(question)
            
            # Format sources already prepared in merge step (truncate content for non-streaming)
            for s in sources:
                content = s.get("content", "")
                if isinstance(content, str) and len(content) > 200:
                    s["content"] = content[:200] + "..."
            
            return {
                "question": question,
                "answer": answer,
                "sources": sources,
                "context_used": len(relevant_docs) > 0,
                "num_sources": len(sources)
            }
            
        except Exception as e:
            logger.error(f"Error in RAG question answering: {e}")
            raise
    
    async def search_documents(
        self,
        query: str,
        user_id: UUID,
        knowledge_base_id: Optional[UUID] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search documents using vector similarity
        
        Args:
            query: Search query
            user_id: User ID for document filtering
            knowledge_base_id: Optional knowledge base ID for filtering
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of matching documents with metadata
        """
        try:
            # Create collection name for user's documents
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
            
            # Perform similarity search
            results = vector_store.similarity_search_with_score(
                query=query,
                k=limit,
                filter=filter_conditions if filter_conditions else None
            )
            
            # Sort by similarity score in descending order (higher scores first)
            results = sorted(results, key=lambda x: x[1], reverse=True)
            
            # Format results
            search_results = []
            for doc, score in results:
                if score <= similarity_threshold:
                    search_results.append({
                        "document_id": doc.metadata.get("document_id"),
                        "document_title": doc.metadata.get("filename", "Unknown"),
                        "content": doc.page_content,
                        "chunk_id": doc.metadata.get("chunk_id"),
                        "chunk_index": doc.metadata.get("chunk_index"),
                        "similarity": float(score),
                        "metadata": doc.metadata
                    })
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error in document search: {e}")
            raise
    
    async def get_conversation_context(
        self,
        conversation_history: List[Dict[str, str]],
        max_messages: int = 10
    ) -> List[Dict[str, str]]:
        """
        Process conversation history for context
        
        Args:
            conversation_history: List of conversation messages
            max_messages: Maximum number of messages to keep
            
        Returns:
            Processed conversation history
        """
        if not conversation_history:
            return []
        
        # Keep only the last max_messages
        recent_history = conversation_history[-max_messages:]
        
        # Format for LangChain
        formatted_history = []
        for msg in recent_history:
            if msg.get("role") == "user":
                formatted_history.append({"role": "human", "content": msg["content"]})
            elif msg.get("role") == "assistant":
                formatted_history.append({"role": "ai", "content": msg["content"]})
        
        return formatted_history