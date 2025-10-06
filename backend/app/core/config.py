"""
Application configuration settings
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Basic app settings
    PROJECT_NAME: str = "HR Agent"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # API settings
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database settings
    DATABASE_URL: str = "postgresql://username:password@localhost:5432/hr_agent"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "hr_agent"
    DATABASE_USER: str = "username"
    DATABASE_PASSWORD: str = "password"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    @property
    def DATABASE_NAME_FROM_URL(self) -> str:
        """Extract database name from DATABASE_URL"""
        if "/" in self.DATABASE_URL:
            return self.DATABASE_URL.split("/")[-1]
        return self.DATABASE_NAME
    
    # Vector database settings
    VECTOR_DIMENSION: int = 2048  # 智谱AI embedding-3 dimension
    
    # LLM settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    
    # Custom LLM settings (for non-OpenAI providers)
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    LLM_MODEL: str = "doubao-1-5-pro-32k-250115"
    
    # Custom Embedding settings
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_BASE_URL: Optional[str] = None
    EMBEDDING_MODEL: str = "embedding-3"
    
    # LangChain settings
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: Optional[str] = None
    
    # Dify Workflow settings
    DIFY_BASE_URL: str = "http://218.78.133.209:85"
    DIFY_API_KEY: Optional[str] = None
    DIFY_USER_ID: str = "hr-agent-user"
    
    # Redis settings (for caching and session)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    model_config = {
        "env_file": Path(__file__).parent.parent.parent / ".env", #正确的.env文件路径
        "case_sensitive": True,
        "extra": "ignore"
    }


settings = Settings()