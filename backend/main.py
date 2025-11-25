"""
HR Agent Backend - FastAPI Application Entry Point
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.v1.api import api_router
from app.core.middleware import setup_middleware
from app.core.logging import setup_logging
from app.core.exception_handlers import setup_exception_handlers
from app.services.email_scheduler import EmailScheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting HR Agent Backend...")
    setup_logging()
    logger.info("Logging configured")
    
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Start email fetch scheduler
    try:
        app.state.email_scheduler = EmailScheduler()
        await app.state.email_scheduler.start()
        logger.info("Email scheduler started")
    except Exception as e:
        logger.warning(f"Email scheduler failed to start: {e}")
    # Ensure default roles
    try:
        from app.core.database import AsyncSessionLocal
        from app.services.role_service import RoleService
        async with AsyncSessionLocal() as db:
            rs = RoleService(db)
            await rs.ensure_default_roles()
            await db.commit()
        logger.info("Default roles ensured")
    except Exception as e:
        logger.warning(f"Ensure default roles failed: {e}")

    logger.info("HR Agent Backend started successfully")
    yield
    
    # Shutdown
    logger.info("Shutting down HR Agent Backend...")
    try:
        # Shutdown email scheduler
        scheduler = getattr(app.state, "email_scheduler", None)
        if scheduler:
            await scheduler.shutdown()
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    logger.info("HR Agent Backend shutdown complete")


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="HR Agent - AI-powered Human Resources Assistant",
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan
    )

    # Setup exception handlers
    setup_exception_handlers(app)

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup custom middleware
    setup_middleware(app)

    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Add root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information"""
        return {
            "message": "Welcome to HR Agent API",
            "version": settings.VERSION,
            "docs": f"{settings.API_V1_STR}/docs",
            "redoc": f"{settings.API_V1_STR}/redoc",
            "health": f"{settings.API_V1_STR}/health"
        }

    return app


app = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
