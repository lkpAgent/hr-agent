"""
Logging configuration
"""
import logging
import logging.config
import sys
import os
from pathlib import Path

from app.core.config import settings


class SafeStreamHandler(logging.StreamHandler):
    """
    A StreamHandler that handles encoding errors gracefully
    """
    def emit(self, record):
        try:
            super().emit(record)
        except UnicodeEncodeError:
            # If encoding fails, replace problematic characters
            try:
                msg = self.format(record)
                # Replace problematic Unicode characters with safe alternatives
                safe_msg = msg.encode('utf-8', errors='replace').decode('utf-8')
                self.stream.write(safe_msg + self.terminator)
                self.flush()
            except Exception:
                # Last resort: just print a simple error message
                self.stream.write(f"[ENCODING ERROR] Log message could not be displayed\n")
                self.flush()


def setup_logging() -> None:
    """
    Setup application logging configuration
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Set console encoding to UTF-8 if possible (Windows)
    if os.name == 'nt':  # Windows
        try:
            # Try to set console to UTF-8
            os.system('chcp 65001 >nul 2>&1')
        except:
            pass
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": settings.LOG_FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "()": SafeStreamHandler,
                "level": settings.LOG_LEVEL,
                "formatter": "default",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "detailed",
                "filename": "logs/hr_agent.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": "logs/hr_agent_error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "": {  # root logger
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["file"],
                "propagate": False,
            },
        },
    }
    
    logging.config.dictConfig(logging_config)
    logger = logging.getLogger(__name__)
    logger.info("Logging configuration setup complete")


# Create a global logger instance
logger = logging.getLogger(__name__)