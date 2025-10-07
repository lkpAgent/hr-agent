"""
Scoring Criteria schemas for API request/response validation
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.scoring_criteria import ScoringStatus


class ScoringCriteriaBase(BaseModel):
    """Base schema for scoring criteria"""
    title: str
    job_title: Optional[str] = None
    content: str
    criteria_data: Optional[Dict[str, Any]] = None
    total_score: Optional[str] = "100"
    scoring_dimensions: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = "draft"
    meta_data: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    workflow_type: Optional[str] = "scoring_criteria_generation"
    job_description_id: Optional[UUID] = None


class ScoringCriteriaCreate(ScoringCriteriaBase):
    """Schema for creating a new Scoring Criteria"""
    pass


class ScoringCriteriaUpdate(BaseModel):
    """Schema for updating a Scoring Criteria"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    criteria_data: Optional[Dict[str, Any]] = None
    total_score: Optional[str] = Field(None, max_length=10)
    scoring_dimensions: Optional[List[Dict[str, Any]]] = None
    status: Optional[ScoringStatus] = None
    meta_data: Optional[Dict[str, Any]] = None
    job_description_id: Optional[UUID] = None


class ScoringCriteriaInDB(ScoringCriteriaBase):
    """Schema for Scoring Criteria in database"""
    id: UUID
    user_id: UUID
    workflow_type: str
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class ScoringCriteriaResponse(ScoringCriteriaInDB):
    """Schema for Scoring Criteria API response"""
    pass


class ScoringCriteriaListResponse(BaseModel):
    """Schema for Scoring Criteria list response"""
    items: List[ScoringCriteriaResponse]
    total: int
    page: int
    size: int
    pages: int