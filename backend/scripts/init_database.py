#!/usr/bin/env python3
"""
HR Agent Database Initialization Script

This script initializes the database with all required tables and creates an initial admin user.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.database import Base
from app.models import user, conversation, knowledge_base, document
from app.core.security import get_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Database initialization utility"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
    
    def create_database(self):
        """Create the database if it doesn't exist"""
        try:
            # Extract database name from URL
            db_name = settings.DATABASE_URL.split('/')[-1]
            
            # Connect to postgres database to create our database
            postgres_url = settings.DATABASE_URL.replace(f"/{db_name}", "/postgres")
            engine = create_engine(postgres_url)
            
            with engine.connect() as conn:
                # Check if database exists
                result = conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                    {"db_name": db_name}
                )
                
                if not result.fetchone():
                    # Create database
                    conn.execute(text("COMMIT"))  # End transaction
                    conn.execute(text(f"CREATE DATABASE {db_name}"))
                    logger.info(f"✅ Database '{db_name}' created successfully")
                else:
                    logger.info(f"ℹ️  Database '{db_name}' already exists")
            
            engine.dispose()
            
        except Exception as e:
            logger.error(f"❌ Error creating database: {e}")
            raise
    
    def install_extensions(self):
        """Install required PostgreSQL extensions"""
        try:
            engine = create_engine(settings.DATABASE_URL)
            
            with engine.begin() as conn:
                # Install uuid-ossp extension
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
                logger.info("✅ uuid-ossp extension installed")
                
                # Install vector extension (pgvector)
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                logger.info("✅ vector extension installed")
            
            engine.dispose()
            
        except Exception as e:
            logger.error(f"❌ Error installing extensions: {e}")
            raise
    
    def create_tables(self):
        """Create all database tables"""
        try:
            engine = create_engine(settings.DATABASE_URL)
            # Create all tables
            Base.metadata.create_all(bind=engine)
            logger.info("✅ All database tables created successfully")
            engine.dispose()
            
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            raise
    
    def create_admin_user(self, email: str = "admin@example.com", password: str = "admin123", username: str = "admin"):
        """Create initial admin user"""
        try:
            engine = create_engine(settings.DATABASE_URL)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            try:
                # Import User model and UserRole enum
                from app.models.user import User, UserRole
                
                # Check if admin user already exists
                existing_user = session.query(User).filter(
                    (User.email == email) | (User.username == username)
                ).first()
                
                if existing_user:
                    logger.info(f"ℹ️  Admin user '{email}' or '{username}' already exists")
                    return
                
                # Create admin user using ORM
                hashed_password = get_password_hash(password)
                admin_user = User(
                    username=username,
                    email=email,
                    full_name="System Administrator",
                    hashed_password=hashed_password,
                    role=UserRole.ADMIN,
                    is_superuser=True,
                    is_verified=True,
                    department="IT",
                    position="System Administrator",
                    employee_id="ADMIN003"
                )
                
                session.add(admin_user)
                session.commit()
                session.refresh(admin_user)
                
                logger.info(f"✅ Admin user created successfully")
                logger.info(f"👤 Username: {username}")
                logger.info(f"📧 Email: {email}")
                logger.info(f"🔑 Password: {password}")
                logger.info(f"🆔 User ID: {admin_user.id}")
                
            finally:
                session.close()
                engine.dispose()
                
        except Exception as e:
            logger.error(f"❌ Error creating admin user: {e}")
            raise
    
    def initialize_complete_database(self, admin_email: str = "admin@example.com", admin_password: str = "admin123", admin_username: str = "admin"):
        """Complete database initialization"""
        try:
            logger.info("🚀 Starting complete database initialization...")
            
            # Step 1: Create database
            self.create_database()
            
            # Step 2: Install extensions
            self.install_extensions()
            
            # Step 3: Create tables
            self.create_tables()
            
            # Step 4: Create admin user
            self.create_admin_user(admin_email, admin_password, admin_username)
            
            logger.info("🎉 Database initialization completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument("command", choices=["init", "create-admin"], help="Command to execute")
    parser.add_argument("--email", default="admin3@example.com", help="Admin email")
    parser.add_argument("--password", default="admin123", help="Admin password")
    parser.add_argument("--username", default="admin3", help="Admin username")
    
    args = parser.parse_args()
    
    initializer = DatabaseInitializer()
    
    try:
        if args.command == "init":
            initializer.initialize_complete_database(
                admin_email=args.email,
                admin_password=args.password,
                admin_username=args.username
            )
        elif args.command == "create-admin":
            initializer.create_admin_user(email=args.email, password=args.password, username=args.username)
            
    except Exception as e:
        logger.error(f"❌ Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()