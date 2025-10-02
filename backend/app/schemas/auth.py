"""
Authentication schemas for request/response validation
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class UserLogin(BaseModel):
    """User login request schema"""
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    """User registration request schema"""
    email: EmailStr
    password: str
    full_name: str
    department: Optional[str] = None
    position: Optional[str] = None
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserCreate(BaseModel):
    """User creation schema (alias for UserRegister)"""
    email: EmailStr
    password: str
    full_name: str
    department: Optional[str] = None
    position: Optional[str] = None
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token data schema for internal use"""
    user_id: Optional[str] = None
    email: Optional[str] = None


class PasswordReset(BaseModel):
    """Password reset request schema"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str
    new_password: str
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class ChangePassword(BaseModel):
    """Change password request schema"""
    current_password: str
    new_password: str
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v