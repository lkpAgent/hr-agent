"""
Database models package
"""

# Import all models to ensure proper relationship mapping
from app.models.base import BaseModel
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.models.knowledge_base import KnowledgeBase, FAQ
from app.models.conversation import Conversation, Message
from app.models.job_description import JobDescription
from app.models.scoring_criteria import ScoringCriteria
from app.models.resume_evaluation import ResumeEvaluation

# Export all models
__all__ = [
    "BaseModel",
    "User", 
    "Document",
    "DocumentChunk",
    "KnowledgeBase",
    "FAQ",
    "Conversation",
    "Message",
    "JobDescription",
    "ScoringCriteria",
    "ResumeEvaluation"
]