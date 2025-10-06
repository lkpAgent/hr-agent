"""
Job Description model for storing generated job descriptions
"""
from sqlalchemy import Column, String, Text, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class JDStatus(str, enum.Enum):
    """Job Description status enumeration"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class JobDescription(BaseModel):
    """Job Description model for storing generated job descriptions"""
    
    __tablename__ = "job_descriptions"
    
    # Basic information
    title = Column(String(255), nullable=False)
    department = Column(String(100), nullable=True)
    location = Column(String(100), nullable=True)
    salary_range = Column(String(100), nullable=True)
    experience_level = Column(String(100), nullable=True)  # 工作经验要求
    education = Column(String(100), nullable=True)   # 学历要求
    job_type = Column(String(50), nullable=True)     # 工作性质（全职/兼职/实习等）
    skills = Column(JSON, nullable=True)             # 技能要求列表
    
    # Content
    content = Column(Text, nullable=False)  # The generated JD content in markdown format
    requirements = Column(Text, nullable=True)  # Original requirements used for generation
    
    # Status and metadata
    status = Column(Enum(JDStatus), default=JDStatus.DRAFT, nullable=False)
    meta_data = Column(JSON, nullable=True)  # Additional metadata like generation parameters
    
    # Generation context
    conversation_id = Column(String(255), nullable=True)  # Link to the conversation that generated this JD
    workflow_type = Column(String(50), default="jd_generation", nullable=False)
    
    # Relationships
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_by_user = relationship("User")
    
    def __repr__(self):
        return f"<JobDescription(title='{self.title}', status='{self.status}')>"