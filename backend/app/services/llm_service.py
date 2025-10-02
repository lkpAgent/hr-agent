"""
LLM service for AI interactions using LangChain
"""
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain_openai import OpenAI, ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.config import settings

logger = logging.getLogger(__name__)


class StreamingCallbackHandler(AsyncCallbackHandler):
    """Callback handler for streaming responses"""
    
    def __init__(self):
        self.tokens = []
    
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Handle new token from LLM"""
        self.tokens.append(token)


class LLMService:
    """Service for LLM interactions"""
    
    def __init__(self):
        self.chat_model = ChatOpenAI(
            model_name=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.7,
            streaming=True
        )
        
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # HR-specific system prompt
        self.system_prompt = """You are an AI assistant specialized in Human Resources. 
        You help employees and HR professionals with:
        - HR policies and procedures
        - Employee benefits and compensation
        - Performance management
        - Recruitment and hiring
        - Training and development
        - Workplace compliance and regulations
        - Employee relations and conflict resolution
        
        Always provide accurate, helpful, and professional responses. 
        If you're unsure about specific company policies, recommend consulting with HR directly.
        Maintain confidentiality and be sensitive to employee concerns."""
    
    async def generate_response(
        self,
        message: str,
        conversation_history: List[Dict[str, str]] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Generate a response using the chat model
        """
        try:
            messages = [SystemMessage(content=self.system_prompt)]
            
            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-10:]:  # Keep last 10 messages
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
            
            # Add context if provided
            if context:
                context_message = f"Relevant context: {context}\n\nUser question: {message}"
                messages.append(HumanMessage(content=context_message))
            else:
                messages.append(HumanMessage(content=message))
            
            response = await self.chat_model.agenerate([messages])
            return response.generations[0][0].text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    async def stream_response(
        self,
        message: str,
        conversation_history: List[Dict[str, str]] = None,
        context: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response
        """
        try:
            callback = StreamingCallbackHandler()
            
            messages = [SystemMessage(content=self.system_prompt)]
            
            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-10:]:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
            
            # Add context if provided
            if context:
                context_message = f"Relevant context: {context}\n\nUser question: {message}"
                messages.append(HumanMessage(content=context_message))
            else:
                messages.append(HumanMessage(content=message))
            
            # Stream the response
            async for token in self.chat_model.astream(messages, callbacks=[callback]):
                yield token.content
                
        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text
        """
        try:
            embedding = await self.embeddings.aembed_query(text)
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        """
        try:
            embeddings = await self.embeddings.aembed_documents(texts)
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    async def summarize_text(self, text: str, max_length: int = 200) -> str:
        """
        Summarize text using LLM
        """
        try:
            prompt = f"""Please provide a concise summary of the following text in no more than {max_length} words:

{text}

Summary:"""
            
            messages = [HumanMessage(content=prompt)]
            response = await self.chat_model.agenerate([messages])
            return response.generations[0][0].text.strip()
            
        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            raise
    
    async def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text
        """
        try:
            prompt = f"""Extract the most important keywords from the following text. 
Return only the keywords separated by commas, maximum {max_keywords} keywords:

{text}

Keywords:"""
            
            messages = [HumanMessage(content=prompt)]
            response = await self.chat_model.agenerate([messages])
            keywords_text = response.generations[0][0].text.strip()
            
            # Parse keywords
            keywords = [kw.strip() for kw in keywords_text.split(",")]
            return keywords[:max_keywords]
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            raise
    
    async def generate_suggestions(self, query: str, context: str = "") -> List[str]:
        """
        Generate query suggestions based on input
        """
        try:
            prompt = f"""Based on the following HR-related query, suggest 5 related questions that users might want to ask:

Query: {query}
Context: {context}

Provide 5 short, relevant questions (one per line):"""
            
            messages = [HumanMessage(content=prompt)]
            response = await self.chat_model.agenerate([messages])
            suggestions_text = response.generations[0][0].text.strip()
            
            # Parse suggestions
            suggestions = [s.strip() for s in suggestions_text.split("\n") if s.strip()]
            return suggestions[:5]
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            raise