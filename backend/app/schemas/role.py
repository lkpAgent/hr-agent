"""
Pydantic schemas for roles
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    permissions: Optional[List[str]] = None


class RoleCreate(RoleBase):
    is_builtin: bool = False


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    permissions: Optional[List[str]] = None


class RoleInDB(RoleBase):
    id: UUID
    is_builtin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Role(RoleInDB):
    pass

