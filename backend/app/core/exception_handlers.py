"""
Exception handlers for the application
"""
import logging
from typing import Union
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError

from app.core.exceptions import BaseHTTPException, DatabaseIntegrityError, DatabaseError

logger = logging.getLogger(__name__)


async def base_http_exception_handler(request: Request, exc: BaseHTTPException) -> JSONResponse:
    """Handle custom base HTTP exceptions"""
    logger.error(
        f"HTTP Exception: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "type": exc.__class__.__name__,
                "details": exc.details,
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    logger.error(
        f"HTTP Exception: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "type": "HTTPException",
            }
        }
    )


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle Starlette HTTP exceptions"""
    logger.error(
        f"Starlette HTTP Exception: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "type": "HTTPException",
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors"""
    logger.warning(
        f"Validation Error: {exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors(),
        }
    )
    
    # Format validation errors
    formatted_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "message": "Validation failed",
                "type": "ValidationError",
                "details": {
                    "errors": formatted_errors
                }
            }
        }
    )


async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    logger.warning(
        f"Pydantic Validation Error: {exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors(),
        }
    )
    
    # Format validation errors
    formatted_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "message": "Data validation failed",
                "type": "ValidationError",
                "details": {
                    "errors": formatted_errors
                }
            }
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors"""
    logger.error(
        f"Database Error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": exc.__class__.__name__,
        },
        exc_info=True
    )
    
    # Handle specific SQLAlchemy exceptions
    if isinstance(exc, IntegrityError):
        # Check for common integrity constraint violations
        error_message = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
        
        if "unique constraint" in error_message.lower():
            return JSONResponse(
                status_code=409,
                content={
                    "error": {
                        "message": "Resource already exists",
                        "type": "ConflictError",
                        "details": {
                            "constraint": "unique_constraint_violation"
                        }
                    }
                }
            )
        elif "foreign key constraint" in error_message.lower():
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "message": "Invalid reference to related resource",
                        "type": "ValidationError",
                        "details": {
                            "constraint": "foreign_key_constraint_violation"
                        }
                    }
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "message": "Data integrity constraint violated",
                        "type": "ValidationError",
                        "details": {
                            "constraint": "integrity_constraint_violation"
                        }
                    }
                }
            )
    
    # Generic database error
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Database operation failed",
                "type": "DatabaseError",
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other unhandled exceptions"""
    logger.error(
        f"Unhandled Exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": exc.__class__.__name__,
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "An unexpected error occurred",
                "type": "InternalServerError",
            }
        }
    )


def setup_exception_handlers(app):
    """Setup all exception handlers"""
    
    # Custom exception handlers
    app.add_exception_handler(BaseHTTPException, base_http_exception_handler)
    
    # FastAPI and Starlette exception handlers
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    
    # Validation exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    
    # Database exception handlers
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    
    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers setup complete")