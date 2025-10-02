"""
Custom exception classes
"""
from typing import Any, Dict, Optional


class BaseHTTPException(Exception):
    """Base HTTP exception class"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseHTTPException):
    """Validation error exception"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class AuthenticationError(BaseHTTPException):
    """Authentication error exception"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(BaseHTTPException):
    """Authorization error exception"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=403)


class NotFoundError(BaseHTTPException):
    """Resource not found exception"""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ConflictError(BaseHTTPException):
    """Resource conflict exception"""
    
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=409)


class RateLimitError(BaseHTTPException):
    """Rate limit exceeded exception"""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class InternalServerError(BaseHTTPException):
    """Internal server error exception"""
    
    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, status_code=500)


class ServiceUnavailableError(BaseHTTPException):
    """Service unavailable exception"""
    
    def __init__(self, message: str = "Service unavailable"):
        super().__init__(message, status_code=503)


# User-related exceptions
class UserNotFoundError(NotFoundError):
    """User not found exception"""
    
    def __init__(self, user_id: str = None):
        message = f"User {user_id} not found" if user_id else "User not found"
        super().__init__(message)


class UserAlreadyExistsError(ConflictError):
    """User already exists exception"""
    
    def __init__(self, field: str = "email"):
        super().__init__(f"User with this {field} already exists")


class InvalidCredentialsError(AuthenticationError):
    """Invalid credentials exception"""
    
    def __init__(self):
        super().__init__("Invalid email or password")


class InactiveUserError(AuthenticationError):
    """Inactive user exception"""
    
    def __init__(self):
        super().__init__("User account is inactive")


class InvalidTokenError(AuthenticationError):
    """Invalid token exception"""
    
    def __init__(self):
        super().__init__("Invalid or expired token")


class TokenExpiredError(AuthenticationError):
    """Token expired exception"""
    
    def __init__(self):
        super().__init__("Token has expired")


# Document-related exceptions
class DocumentNotFoundError(NotFoundError):
    """Document not found exception"""
    
    def __init__(self, document_id: str = None):
        message = f"Document {document_id} not found" if document_id else "Document not found"
        super().__init__(message)


class DocumentUploadError(ValidationError):
    """Document upload error exception"""
    
    def __init__(self, message: str = "Document upload failed"):
        super().__init__(message)


class UnsupportedFileTypeError(ValidationError):
    """Unsupported file type exception"""
    
    def __init__(self, file_type: str = None):
        message = f"Unsupported file type: {file_type}" if file_type else "Unsupported file type"
        super().__init__(message)


class FileSizeExceededError(ValidationError):
    """File size exceeded exception"""
    
    def __init__(self, max_size: str = None):
        message = f"File size exceeds maximum allowed size of {max_size}" if max_size else "File size too large"
        super().__init__(message)


class DocumentProcessingError(InternalServerError):
    """Document processing error exception"""
    
    def __init__(self, message: str = "Document processing failed"):
        super().__init__(message)


# Conversation-related exceptions
class ConversationNotFoundError(NotFoundError):
    """Conversation not found exception"""
    
    def __init__(self, conversation_id: str = None):
        message = f"Conversation {conversation_id} not found" if conversation_id else "Conversation not found"
        super().__init__(message)


class MessageNotFoundError(NotFoundError):
    """Message not found exception"""
    
    def __init__(self, message_id: str = None):
        message = f"Message {message_id} not found" if message_id else "Message not found"
        super().__init__(message)


class ConversationAccessDeniedError(AuthorizationError):
    """Conversation access denied exception"""
    
    def __init__(self):
        super().__init__("Access to this conversation is denied")


# Knowledge base-related exceptions
class KnowledgeBaseNotFoundError(NotFoundError):
    """Knowledge base not found exception"""
    
    def __init__(self, kb_id: str = None):
        message = f"Knowledge base {kb_id} not found" if kb_id else "Knowledge base not found"
        super().__init__(message)


class FAQNotFoundError(NotFoundError):
    """FAQ not found exception"""
    
    def __init__(self, faq_id: str = None):
        message = f"FAQ {faq_id} not found" if faq_id else "FAQ not found"
        super().__init__(message)


# LLM-related exceptions
class LLMServiceError(InternalServerError):
    """LLM service error exception"""
    
    def __init__(self, message: str = "LLM service error"):
        super().__init__(message)


class LLMRateLimitError(RateLimitError):
    """LLM rate limit exceeded exception"""
    
    def __init__(self):
        super().__init__("LLM API rate limit exceeded")


class LLMQuotaExceededError(ServiceUnavailableError):
    """LLM quota exceeded exception"""
    
    def __init__(self):
        super().__init__("LLM API quota exceeded")


class EmbeddingServiceError(InternalServerError):
    """Embedding service error exception"""
    
    def __init__(self, message: str = "Embedding service error"):
        super().__init__(message)


# Database-related exceptions
class DatabaseError(InternalServerError):
    """Database error exception"""
    
    def __init__(self, message: str = "Database error"):
        super().__init__(message)


class DatabaseConnectionError(ServiceUnavailableError):
    """Database connection error exception"""
    
    def __init__(self):
        super().__init__("Database connection failed")


class DatabaseIntegrityError(ConflictError):
    """Database integrity error exception"""
    
    def __init__(self, message: str = "Database integrity constraint violated"):
        super().__init__(message)


# Search-related exceptions
class SearchError(InternalServerError):
    """Search error exception"""
    
    def __init__(self, message: str = "Search operation failed"):
        super().__init__(message)


class VectorSearchError(SearchError):
    """Vector search error exception"""
    
    def __init__(self, message: str = "Vector search failed"):
        super().__init__(message)


# Configuration-related exceptions
class ConfigurationError(InternalServerError):
    """Configuration error exception"""
    
    def __init__(self, message: str = "Configuration error"):
        super().__init__(message)


class MissingConfigurationError(ConfigurationError):
    """Missing configuration exception"""
    
    def __init__(self, config_key: str):
        super().__init__(f"Missing required configuration: {config_key}")


# External service exceptions
class ExternalServiceError(ServiceUnavailableError):
    """External service error exception"""
    
    def __init__(self, service_name: str = "external service"):
        super().__init__(f"{service_name} is currently unavailable")


class ExternalServiceTimeoutError(ServiceUnavailableError):
    """External service timeout exception"""
    
    def __init__(self, service_name: str = "external service"):
        super().__init__(f"{service_name} request timed out")