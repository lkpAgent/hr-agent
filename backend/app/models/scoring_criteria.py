"""
Scoring Criteria model for storing resume scoring criteria
"""
from sqlalchemy import Column, String, Text, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class ScoringStatus(str, enum.Enum):
    """Scoring Criteria status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ScoringCriteria(BaseModel):
    """Scoring Criteria model for storing resume scoring criteria"""
    
    __tablename__ = "scoring_criteria"
    
    # Basic information
    title = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=True)  # 关联的职位名称
    
    # Content
    content = Column(Text, nullable=False)  # The generated scoring criteria content in markdown format
    criteria_data = Column(JSON, nullable=True)  # Structured scoring criteria data
    
    # Scoring configuration
    total_score = Column(String(10), default="100", nullable=False)  # 总分
    scoring_dimensions = Column(JSON, nullable=True)  # 评分维度配置
    
    # Status and metadata
    status = Column(Enum(ScoringStatus), default=ScoringStatus.DRAFT, nullable=False)
    meta_data = Column(JSON, nullable=True)  # Additional metadata like generation parameters
    
    # Generation context
    conversation_id = Column(String(255), nullable=True)  # Link to the conversation that generated this criteria
    workflow_type = Column(String(50), default="scoring_criteria_generation", nullable=False)
    
    # Relationships
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_by_user = relationship("User")
    
    # Optional relationship to JobDescription
    job_description_id = Column(UUID(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=True)
    job_description = relationship("JobDescription")
    
    def __repr__(self):
        return f"<ScoringCriteria(title='{self.title}', status='{self.status}')>"