"""
Role model for RBAC
"""
from sqlalchemy import Column, String, Boolean, JSON
from app.models.base import BaseModel
from sqlalchemy.orm import relationship


class Role(BaseModel):
    __tablename__ = "roles"

    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_builtin = Column(Boolean, default=False, nullable=False)
    permissions = Column(JSON, nullable=True)  # list of permission ids
    users = relationship("User", secondary="user_roles", back_populates="roles")

    def __repr__(self):
        return f"<Role(name='{self.name}', builtin={self.is_builtin})>"
