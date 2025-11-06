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

    async def extract_keywords_and_tags(self, text: str, max_items: int = 8) -> Dict[str, List[str]]:
        """Extract 5-8 per-chunk keywords and tags.
        Tags should include explicit Chinese ordinal phrases like "第一条"、"第一点"、"第二条"等（如果文本中出现），
        but exclude pure numeric markers (e.g., "1", "2", "3", "一", "二" without a descriptive suffix).
        Return a dict: {"keywords": [...], "tags": [...]}.
        """
        try:
            prompt = (
                "请从下面的段落中提取5-8个关键词和标签。\n"
                "要求：\n"
                "- 关键词：能概括段落核心概念或主题，避免过于通用词（如：具体、以及、因此）。\n"
                "- 标签：如果段落中有明确的中文序号短语（如‘第一条’、‘第一点’、‘第二条’、‘第三点’等），请将这些短语作为标签；仅有纯数字或字母序号（如‘1.’、‘(2)’、‘A.’）不要提取。\n"
                "- 只返回JSON，不要解释。\n"
                '- JSON格式：{"keywords": [..], "tags": [..]}\n'
                f"段落：\n{text}\n\n"
                "请返回："
            )
            response = await self.client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=400
            )
            content = response.choices[0].message.content.strip()

            # Robust JSON parsing
            import json
            result: Dict[str, List[str]] = {"keywords": [], "tags": []}
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    kws = parsed.get("keywords", [])
                    tags = parsed.get("tags", [])
                    if isinstance(kws, list):
                        result["keywords"] = [str(x).strip() for x in kws if str(x).strip()]
                    if isinstance(tags, list):
                        result["tags"] = [str(x).strip() for x in tags if str(x).strip()]
            except Exception:
                # Fallback: try comma/line splitting
                lines = [x.strip() for x in content.replace("\r", "").split("\n") if x.strip()]
                # naive split: lines may contain "keywords: ..." or "tags: ..."
                for line in lines:
                    lower = line.lower()
                    if lower.startswith("keywords") or lower.startswith("关键词"):
                        items = line.split(":", 1)
                        if len(items) > 1:
                            result["keywords"] = [x.strip() for x in items[1].split(",") if x.strip()]
                    elif lower.startswith("tags") or lower.startswith("标签"):
                        items = line.split(":", 1)
                        if len(items) > 1:
                            result["tags"] = [x.strip() for x in items[1].split(",") if x.strip()]

            # Post-filtering: enforce limits and remove numeric-only tags
            def is_numeric_only(s: str) -> bool:
                import re
                return bool(re.fullmatch(r"[0-9]+|[一二三四五六七八九十]+", s))

            result["keywords"] = result["keywords"][:max_items]
            result["tags"] = [t for t in result["tags"] if not is_numeric_only(t)][:max_items]

            return result
        except Exception as e:
            logger.error(f"Error extracting keywords and tags: {e}")
            return {"keywords": [], "tags": []}

    async def extract_keywords_tags_combined(self, text: str, max_items: int = 8) -> str:
        """Extract 5-8 combined keywords/tags as a single comma-separated string.
        Include explicit Chinese ordinal phrases like "第一条"、"第一点"、"第二条"等（如果文本中出现），
        but exclude pure numeric markers (e.g., "1", "2", "3", "一", "二" without a descriptive suffix).
        Return e.g.: "关键词A, 关键词B, 第一条, 第二点".
        """
        try:
            prompt = (
                "请从下面的段落中提取5-8个关键词或标签，合并在一行返回。\n"
                "要求：\n"
                "- 关键词：能概括段落核心概念或主题；避免过于通用词。\n"
                "- 标签：若出现明确中文序号短语（如‘第一条’、‘第一点’、‘第二条’），则提取；仅有纯数字或字母序号（如‘1.’、‘(2)’、‘A.’）不要提取。\n"
                "- 只返回逗号分隔的一行结果，不要任何解释或多余文本。\n"
                "示例输出：关键词A, 关键词B, 第一条, 第二点\n"
                f"段落：\n{text}\n\n"
                "请返回："
            )
            response = await self.client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=300
            )
            content = response.choices[0].message.content.strip()

            # Normalize to a comma-separated list
            raw_items = [x.strip() for x in content.replace("\r", "").replace("\n", " ").split(",")]
            items = [x for x in raw_items if x]

            # Filter numeric-only tokens
            import re
            def is_numeric_only(s: str) -> bool:
                return bool(re.fullmatch(r"[0-9]+|[一二三四五六七八九十]+", s))
            items = [x for x in items if not is_numeric_only(x)]

            # Deduplicate preserving order and limit
            seen = set()
            deduped = []
            for x in items:
                if x not in seen:
                    seen.add(x)
                    deduped.append(x)
            deduped = deduped[:max_items]

            return ", ".join(deduped)
        except Exception as e:
            logger.error(f"Error extracting combined keywords/tags: {e}")
            return ""
    
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