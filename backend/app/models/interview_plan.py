"""
Interview Plan model for storing interview plan information
"""
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class InterviewPlan(BaseModel):
    """面试方案模型"""
    
    __tablename__ = "interview_plans"
    
    # 核心字段
    candidate_name = Column(String(100), nullable=False)  # 候选人姓名
    candidate_position = Column(String(200), nullable=False)  # 应聘岗位
    content = Column(Text, nullable=False)  # 面试方案内容
    
    # 关联字段
    resume_evaluation_id = Column(UUID(as_uuid=True), ForeignKey("resume_evaluations.id"), nullable=False)  # 关联的简历评价ID
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # 创建用户ID
    
    # 关联关系
    resume_evaluation = relationship("ResumeEvaluation", back_populates="interview_plans")
    user = relationship("User", back_populates="interview_plans")
    
    def __repr__(self):
        return f"<InterviewPlan(id={self.id}, title={self.title}, candidate_name={self.candidate_name})>"