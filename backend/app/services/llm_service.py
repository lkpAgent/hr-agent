"""
LLM service for AI interactions using OpenAI client
"""
import logging
import httpx
import asyncio
import openai
from typing import List, Dict, Any, Optional, AsyncGenerator
# Removed LangChain imports to avoid compatibility issues

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM interactions"""
    
    def __init__(self):
        # Initialize OpenAI client with configured LLM
        llm_api_key = getattr(settings, 'LLM_API_KEY', None) or settings.OPENAI_API_KEY
        llm_base_url = getattr(settings, 'LLM_BASE_URL', None) or 'https://api.openai.com/v1'
        self.llm_model = getattr(settings, 'LLM_MODEL', 'gpt-3.5-turbo')
        
        # Only pass base_url if it's not the default OpenAI URL
        client_kwargs = {'api_key': llm_api_key}
        if llm_base_url != 'https://api.openai.com/v1':
            client_kwargs['base_url'] = llm_base_url
            
        self.client = openai.AsyncOpenAI(**client_kwargs)
        
        # For embeddings, we'll use a custom implementation since we have a different API
        self.embedding_api_key = settings.EMBEDDING_API_KEY or settings.OPENAI_API_KEY
        self.embedding_base_url = settings.EMBEDDING_BASE_URL or 'https://api.openai.com/v1'
        self.embedding_model = settings.EMBEDDING_MODEL or 'text-embedding-ada-002'
        
        # Debug logging
        logger.info(f"Settings EMBEDDING_API_KEY: {'***' if settings.EMBEDDING_API_KEY else 'None'}")
        logger.info(f"Settings EMBEDDING_BASE_URL: {settings.EMBEDDING_BASE_URL}")
        logger.info(f"Settings EMBEDDING_MODEL: {settings.EMBEDDING_MODEL}")
        logger.info(f"Embedding config - API Key: {'***' if self.embedding_api_key else 'None'}")
        logger.info(f"Embedding config - Base URL: {self.embedding_base_url}")
        logger.info(f"Embedding config - Model: {self.embedding_model}")
        
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
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-10:]:  # Keep last 10 messages
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Add context if provided
            if context:
                context_message = f"Relevant context: {context}\n\nUser question: {message}"
                messages.append({"role": "user", "content": context_message})
            else:
                messages.append({"role": "user", "content": message})
            
            response = await self.client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
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
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-10:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Add context if provided
            if context:
                context_message = f"Relevant context: {context}\n\nUser question: {message}"
                messages.append({"role": "user", "content": context_message})
            else:
                messages.append({"role": "user", "content": message})
            
            # Stream the response
            stream = await self.client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                
        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using configured embedding API
        """
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.embedding_api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": self.embedding_model,
                    "input": text
                }
                
                response = await client.post(
                    f"{self.embedding_base_url}/embeddings",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["data"][0]["embedding"]
                else:
                    logger.error(f"Embedding API error: {response.status_code} - {response.text}")
                    raise Exception(f"Embedding API error: {response.status_code}")
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def generate_embedding_sync(self, text: str) -> List[float]:
        """
        Synchronous version of generate_embedding for use in non-async contexts
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.generate_embedding(text))
        except RuntimeError:
            # If no event loop is running, create a new one
            return asyncio.run(self.generate_embedding(text))
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        """
        try:
            embeddings = []
            for text in texts:
                embedding = await self.generate_embedding(text)
                embeddings.append(embedding)
                # Add small delay to avoid rate limiting
                await asyncio.sleep(0.1)
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
            
            response = await self.client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=max_length * 2  # Allow some buffer for tokens
            )
            
            return response.choices[0].message.content.strip()
            
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
            
            response = await self.client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            keywords_text = response.choices[0].message.content.strip()
            
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
            
            response = await self.client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            suggestions_text = response.choices[0].message.content.strip()
            
            # Parse suggestions
            suggestions = [s.strip() for s in suggestions_text.split("\n") if s.strip()]
            return suggestions[:5]
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            raise