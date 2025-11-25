"""
Email configuration and fetch log models
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import BaseModel


class EmailConfig(BaseModel):
    """Recruitment email configuration"""

    __tablename__ = "email_configs"

    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)

    # IMAP config
    imap_server = Column(String(255), nullable=False)
    imap_port = Column(Integer, nullable=False, default=993)
    imap_ssl = Column(Boolean, nullable=False, default=True)

    # SMTP config
    smtp_server = Column(String(255), nullable=True)
    smtp_port = Column(Integer, nullable=True, default=587)
    smtp_ssl = Column(Boolean, nullable=False, default=True)

    # Auth
    password = Column(String(512), nullable=True)

    # Fetch settings
    fetch_interval = Column(Integer, nullable=False, default=30)
    auto_fetch = Column(Boolean, nullable=False, default=False)

    # Status
    status = Column(String(50), nullable=False, default="active")
    connection_status = Column(String(50), nullable=False, default="unknown")
    last_fetch_at = Column(DateTime, nullable=True)

    # Relationships
    logs = relationship("EmailFetchLog", back_populates="email_config", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<EmailConfig(email='{self.email}', status='{self.status}', connection='{self.connection_status}')>"


class EmailFetchLog(BaseModel):
    """Logs for email fetch operations"""

    __tablename__ = "email_fetch_logs"

    email_config_id = Column(UUID(as_uuid=True), ForeignKey("email_configs.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="running")
    emails_found = Column(Integer, nullable=False, default=0)
    resumes_extracted = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)

    email_config = relationship("EmailConfig", back_populates="logs")

    def __repr__(self):
        return f"<EmailFetchLog(config='{self.email_config_id}', status='{self.status}', found={self.emails_found})>"

