#!/usr/bin/env python3
"""
Database Management Script for HR Agent Backend

This script provides utilities for managing the database:
- Initialize database
- Create migrations
- Apply migrations
- Reset database
- Seed initial data
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from alembic.config import Config
from alembic import command
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import logging

from app.core.config import settings
from app.core.database import get_async_engine, init_db
from app.models.base import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database management utilities"""
    
    def __init__(self):
        self.alembic_cfg = Config(str(backend_dir / "alembic.ini"))
        self.alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    
    async def create_database(self):
        """Create the database if it doesn't exist"""
        try:
            # Extract database name from URL
            db_name = settings.DATABASE_NAME
            
            # Connect to postgres database to create our database
            postgres_url = settings.DATABASE_URL.replace(f"/{db_name}", "/postgres")
            engine = create_async_engine(postgres_url)
            
            async with engine.connect() as conn:
                # Check if database exists
                result = await conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                    {"db_name": db_name}
                )
                
                if not result.fetchone():
                    # Create database
                    await conn.execute(text("COMMIT"))  # End transaction
                    await conn.execute(text(f"CREATE DATABASE {db_name}"))
                    logger.info(f"Database '{db_name}' created successfully")
                else:
                    logger.info(f"Database '{db_name}' already exists")
            
            await engine.dispose()
            
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            raise
    
    async def drop_database(self):
        """Drop the database"""
        try:
            db_name = settings.DATABASE_NAME
            postgres_url = settings.DATABASE_URL.replace(f"/{db_name}", "/postgres")
            engine = create_async_engine(postgres_url)
            
            async with engine.connect() as conn:
                # Terminate existing connections
                await conn.execute(text("COMMIT"))
                await conn.execute(
                    text("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = :db_name AND pid <> pg_backend_pid()
                    """),
                    {"db_name": db_name}
                )
                
                # Drop database
                await conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
                logger.info(f"Database '{db_name}' dropped successfully")
            
            await engine.dispose()
            
        except Exception as e:
            logger.error(f"Error dropping database: {e}")
            raise
    
    def create_migration(self, message: str):
        """Create a new migration"""
        try:
            command.revision(self.alembic_cfg, autogenerate=True, message=message)
            logger.info(f"Migration created: {message}")
        except Exception as e:
            logger.error(f"Error creating migration: {e}")
            raise
    
    def apply_migrations(self):
        """Apply all pending migrations"""
        try:
            command.upgrade(self.alembic_cfg, "head")
            logger.info("Migrations applied successfully")
        except Exception as e:
            logger.error(f"Error applying migrations: {e}")
            raise
    
    def downgrade_migration(self, revision: str = "-1"):
        """Downgrade to a specific revision"""
        try:
            command.downgrade(self.alembic_cfg, revision)
            logger.info(f"Downgraded to revision: {revision}")
        except Exception as e:
            logger.error(f"Error downgrading migration: {e}")
            raise
    
    def show_migration_history(self):
        """Show migration history"""
        try:
            command.history(self.alembic_cfg)
        except Exception as e:
            logger.error(f"Error showing migration history: {e}")
            raise
    
    def show_current_revision(self):
        """Show current database revision"""
        try:
            command.current(self.alembic_cfg)
        except Exception as e:
            logger.error(f"Error showing current revision: {e}")
            raise
    
    async def reset_database(self):
        """Reset database (drop, create, migrate)"""
        logger.info("Resetting database...")
        await self.drop_database()
        await self.create_database()
        self.apply_migrations()
        logger.info("Database reset completed")
    
    async def init_database(self):
        """Initialize database (create, migrate)"""
        logger.info("Initializing database...")
        await self.create_database()
        self.apply_migrations()
        logger.info("Database initialization completed")


async def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print("Usage: python db_manager.py <command> [args]")
        print("Commands:")
        print("  init                    - Initialize database")
        print("  reset                   - Reset database (drop and recreate)")
        print("  migrate <message>       - Create new migration")
        print("  upgrade                 - Apply migrations")
        print("  downgrade [revision]    - Downgrade migration")
        print("  history                 - Show migration history")
        print("  current                 - Show current revision")
        return
    
    command = sys.argv[1]
    db_manager = DatabaseManager()
    
    try:
        if command == "init":
            await db_manager.init_database()
        
        elif command == "reset":
            await db_manager.reset_database()
        
        elif command == "migrate":
            if len(sys.argv) < 3:
                print("Error: Migration message required")
                return
            message = " ".join(sys.argv[2:])
            db_manager.create_migration(message)
        
        elif command == "upgrade":
            db_manager.apply_migrations()
        
        elif command == "downgrade":
            revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
            db_manager.downgrade_migration(revision)
        
        elif command == "history":
            db_manager.show_migration_history()
        
        elif command == "current":
            db_manager.show_current_revision()
        
        else:
            print(f"Unknown command: {command}")
            return
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())