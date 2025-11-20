#!/usr/bin/env python3
"""
Admin User Creation Script for HR Agent Backend

This script creates an initial admin user for the HR Agent system.
It can be used to create the first admin account or additional admin accounts.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import uuid
import getpass
from typing import Optional

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import sessionmaker, Session
import logging

from app.core.config import settings
from app.core.security import get_password_hash, verify_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdminCreator:
    """Admin user creation utilities"""
    
    def __init__(self):
        self.engine = None
        self.async_session = None
    
    def create_engine(self):
        """Create database engine"""
        try:
            # Convert async URL to sync URL
            sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
            self.engine = create_engine(
                sync_url,
                echo=False,
                pool_pre_ping=True
            )
            self.session = sessionmaker(
                self.engine, class_=Session, expire_on_commit=False
            )
            logger.info("✅ Database connection established")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise
    
    def check_user_exists(self, username: str, email: str) -> bool:
         """Check if user with username or email already exists"""
         try:
             from app.models.user import User
             with self.session() as session:
                 result = session.execute(
                     select(User).where(
                         (User.username == username) | (User.email == email)
                     )
                 )
                 return result.first() is not None
         except Exception as e:
             logger.error(f"❌ Error checking user existence: {e}")
             raise
    
    def create_admin_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str = "System Administrator",
        department: str = "IT",
        position: str = "System Administrator",
        employee_id: str = None
    ) -> Optional[str]:
        """Create a new admin user"""
        try:
            from app.models.user import User, UserRole
            
            # Check if user already exists
            if self.check_user_exists(username, email):
                logger.error(f"❌ User with username '{username}' or email '{email}' already exists")
                return None
            
            # Generate employee ID if not provided
            if not employee_id:
                employee_id = f"ADMIN{str(uuid.uuid4())[:8].upper()}"
            
            with self.session() as session:
                # Create admin user
                admin_user = User(
                    id=uuid.uuid4(),
                    username=username,
                    email=email,
                    full_name=full_name,
                    hashed_password=get_password_hash(password),
                    role=UserRole.ADMIN,
                    is_superuser=True,
                    is_verified=True,
                    department=department,
                    position=position,
                    employee_id=employee_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                session.add(admin_user)
                session.commit()
                session.refresh(admin_user)
                
                logger.info("✅ Admin user created successfully!")
                logger.info("=" * 50)
                logger.info("ADMIN USER DETAILS:")
                logger.info(f"ID: {admin_user.id}")
                logger.info(f"Username: {admin_user.username}")
                logger.info(f"Email: {admin_user.email}")
                logger.info(f"Full Name: {admin_user.full_name}")
                logger.info(f"Department: {admin_user.department}")
                logger.info(f"Position: {admin_user.position}")
                logger.info(f"Employee ID: {admin_user.employee_id}")
                logger.info(f"Role: {admin_user.role}")
                logger.info(f"Is Superuser: {admin_user.is_superuser}")
                logger.info("=" * 50)
                
                return admin_user
                
        except Exception as e:
            logger.error(f"❌ Error creating admin user: {e}")
            raise
    
    def list_admin_users(self):
        """List all admin users"""
        try:
            from app.models.user import User, UserRole
            
            with self.session() as session:
                result = session.execute(
                    select(User).where(User.role == UserRole.ADMIN)
                )
                admin_users = result.scalars().all()
                
                if not admin_users:
                    logger.info("ℹ️  No admin users found")
                    return
                
                logger.info(f"📋 Found {len(admin_users)} admin user(s):")
                for user in admin_users:
                    logger.info(f"  👤 {user.username} ({user.email}) - ID: {user.id}")
                    logger.info(f"     📧 Email: {user.email}")
                    logger.info(f"     👨‍💼 Full Name: {user.full_name}")
                    logger.info(f"     🆔 Employee ID: {user.employee_id}")
                    logger.info(f"     📅 Created: {user.created_at}")
                    logger.info("     " + "-" * 50)
                    
        except Exception as e:
            logger.error(f"❌ Error listing admin users: {e}")
            raise
    
    def change_user_password(self, username: str, new_password: str):
        """Change user password"""
        try:
            from app.models.user import User
            
            with self.session() as session:
                result = session.execute(
                    select(User).where(User.username == username)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    logger.error(f"❌ User '{username}' not found")
                    return False
                
                user.hashed_password = get_password_hash(new_password)
                user.updated_at = datetime.utcnow()
                
                session.commit()
                logger.info(f"✅ Password updated for user '{username}'")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error changing password: {e}")
            raise
    
    def promote_user_to_admin(self, username: str):
        """Promote existing user to admin"""
        try:
            from app.models.user import User, UserRole
            
            with self.session() as session:
                result = session.execute(
                    select(User).where(User.username == username)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    logger.error(f"❌ User '{username}' not found")
                    return False
                
                user.role = UserRole.ADMIN
                user.is_superuser = True
                user.updated_at = datetime.utcnow()
                
                session.commit()
                logger.info(f"✅ User '{username}' promoted to admin")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error promoting user: {e}")
            raise
    
    def cleanup(self):
        """Cleanup database connection"""
        if self.engine:
            self.engine.dispose()


def get_user_input():
    """Get user input for admin creation"""
    print("🔧 Admin User Creation")
    print("=" * 30)
    
    username = input("Enter username: ").strip()
    if not username:
        print("❌ Username cannot be empty")
        return None
    
    email = input("Enter email: ").strip()
    if not email or "@" not in email:
        print("❌ Please enter a valid email address")
        return None
    
    full_name = input("Enter full name: ").strip()
    if not full_name:
        print("❌ Full name cannot be empty")
        return None
    
    # Get password securely
    while True:
        password = getpass.getpass("Enter password: ")
        if len(password) < 6:
            print("❌ Password must be at least 6 characters long")
            continue
        
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("❌ Passwords do not match")
            continue
        
        break
    
    department = input("Enter department (default: IT): ").strip() or "IT"
    position = input("Enter position (default: System Administrator): ").strip() or "System Administrator"
    employee_id = input("Enter employee ID (optional): ").strip() or None
    
    return {
        "username": username,
        "email": email,
        "full_name": full_name,
        "password": password,
        "department": department,
        "position": position,
        "employee_id": employee_id
    }


def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print("HR Agent Admin User Creation Script")
        print("=" * 40)
        print("Usage: python create_admin.py <command> [options]")
        print("\nCommands:")
        print("  create                  - Create admin user (interactive)")
        print("  create-quick            - Create admin with default credentials")
        print("  create-custom <user> <email> <password> <name>  - Create with specified details")
        print("  list                    - List all admin users")
        print("  change-password <user>  - Change user password")
        print("  promote <user>          - Promote user to admin")
        print("\nExamples:")
        print("  python create_admin.py create")
        print("  python create_admin.py create-quick")
        print("  python create_admin.py create-custom admin admin@company.com admin123 'Admin User'")
        print("  python create_admin.py list")
        print("  python create_admin.py change-password admin")
        print("  python create_admin.py promote john_doe")
        return
    
    command = sys.argv[1]
    creator = AdminCreator()
    
    try:
        creator.create_engine()
        
        if command == "create":
            user_data = get_user_input()
            if user_data:
                creator.create_admin_user(**user_data)
        
        elif command == "create-quick":
            creator.create_admin_user(
                username="testuser",
                email="testuser@hr-agent.com",
                password="test123",
                full_name="System Administrator"
            )
        
        elif command == "create-custom":
            if len(sys.argv) < 6:
                print("❌ Error: Custom creation requires username, email, password, and full name")
                print("Usage: python create_admin.py create-custom <username> <email> <password> <full_name>")
                return
            
            username = sys.argv[2]
            email = sys.argv[3]
            password = sys.argv[4]
            full_name = sys.argv[5]
            
            creator.create_admin_user(
                username=username,
                email=email,
                password=password,
                full_name=full_name
            )
        
        elif command == "list":
            creator.list_admin_users()
        
        elif command == "change-password":
            if len(sys.argv) < 3:
                print("❌ Error: Username required")
                print("Usage: python create_admin.py change-password <username>")
                return
            
            username = sys.argv[2]
            new_password = getpass.getpass(f"Enter new password for '{username}': ")
            creator.change_user_password(username, new_password)
        
        elif command == "promote":
            if len(sys.argv) < 3:
                print("❌ Error: Username required")
                print("Usage: python create_admin.py promote <username>")
                return
            
            username = sys.argv[2]
            creator.promote_user_to_admin(username)
        
        else:
            print(f"❌ Unknown command: {command}")
            return
    
    except Exception as e:
        logger.error(f"❌ Command failed: {e}")
        sys.exit(1)
    finally:
        creator.cleanup()


if __name__ == "__main__":
    main()