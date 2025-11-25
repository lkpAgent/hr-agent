"""
User model for authentication and user management
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    """User roles enumeration"""
    ADMIN = "admin"
    HR_MANAGER = "hr_manager"
    HR_SPECIALIST = "hr_specialist"
    EMPLOYEE = "employee"


class User(BaseModel):
    """User model"""
    
    __tablename__ = "users"
    
    # Basic information
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile information
    phone = Column(String(20), nullable=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    employee_id = Column(String(50), unique=True, nullable=True)
    
    # Role and permissions
    role = Column(Enum(UserRole), default=UserRole.EMPLOYEE, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Additional information
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="uploaded_by", cascade="all, delete-orphan")
    interview_plans = relationship("InterviewPlan", back_populates="user", cascade="all, delete-orphan")
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"
