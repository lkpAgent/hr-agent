#!/usr/bin/env python3
"""
HR Agent Backend Startup Script

This script provides a convenient way to start the application with different configurations.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import uvicorn
from app.core.config import settings


def start_development():
    """Start the application in development mode"""
    print("Starting HR Agent Backend in development mode...")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info",
        access_log=True,
    )


def start_production():
    """Start the application in production mode"""
    print("Starting HR Agent Backend in production mode...")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="warning",
        access_log=False,
        workers=4,
    )


def start_with_gunicorn():
    """Start the application with Gunicorn (production)"""
    print("Starting HR Agent Backend with Gunicorn...")
    cmd = [
        "gunicorn",
        "main:app",
        "-w", "4",
        "-k", "uvicorn.workers.UvicornWorker",
        "--bind", f"{settings.HOST}:{settings.PORT}",
        "--access-logfile", "-",
        "--error-logfile", "-",
        "--log-level", "info"
    ]
    subprocess.run(cmd)


def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print("Usage: python start.py <mode>")
        print("Modes:")
        print("  dev        - Development mode with auto-reload")
        print("  prod       - Production mode with multiple workers")
        print("  gunicorn   - Production mode with Gunicorn")
        return
    
    mode = sys.argv[1]
    
    if mode == "dev":
        start_development()
    elif mode == "prod":
        start_production()
    elif mode == "gunicorn":
        start_with_gunicorn()
    else:
        print(f"Unknown mode: {mode}")
        print("Available modes: dev, prod, gunicorn")


if __name__ == "__main__":
    main()