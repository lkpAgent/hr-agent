"""
Main API router for v1 endpoints
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, conversations, documents, knowledge_base, chat, knowledge_assistant, hr_workflows
from app.api.v1 import resume_evaluation

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(knowledge_base.router, prefix="/knowledge-base", tags=["knowledge-base"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(knowledge_assistant.router, prefix="/knowledge-assistant", tags=["knowledge-assistant"])
api_router.include_router(hr_workflows.router, prefix="/hr-workflows", tags=["hr-workflows"])
api_router.include_router(resume_evaluation.router, prefix="/resume-evaluation", tags=["resume-evaluation"])


@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "HR Agent API is running"}