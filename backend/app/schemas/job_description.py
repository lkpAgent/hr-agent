"""
Job Description schemas for API request/response validation
"""
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.job_description import JDStatus


class JobDescriptionBase(BaseModel):
    """Base schema for job description"""
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    experience_level: Optional[str] = None
    education: Optional[str] = None
    job_type: Optional[str] = None
    skills: Optional[list[str]] = None
    content: str
    requirements: Optional[str] = None
    status: Optional[str] = "draft"
    meta_data: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    workflow_type: Optional[str] = "jd_generation"


class JobDescriptionCreate(JobDescriptionBase):
    """Schema for creating a new Job Description"""
    pass


class JobDescriptionUpdate(BaseModel):
    """Schema for updating a Job Description"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    department: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=100)
    salary_range: Optional[str] = Field(None, max_length=100)
    experience_level: Optional[str] = Field(None, max_length=100)
    education: Optional[str] = Field(None, max_length=100)
    job_type: Optional[str] = Field(None, max_length=50)
    skills: Optional[list[str]] = None
    content: Optional[str] = Field(None, min_length=1)
    requirements: Optional[str] = None
    status: Optional[JDStatus] = None
    meta_data: Optional[Dict[str, Any]] = None


class JobDescriptionInDB(JobDescriptionBase):
    """Schema for Job Description in database"""
    id: UUID
    user_id: UUID
    workflow_type: str
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class JobDescriptionResponse(JobDescriptionInDB):
    """Schema for Job Description API response"""
    pass


class JobDescriptionListResponse(BaseModel):
    """Schema for Job Description list response"""
    items: list[JobDescriptionResponse]
    total: int
    page: int
    size: int
    pages: int