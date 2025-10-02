#!/usr/bin/env python3
"""
Simple Admin User Creation Script for HR Agent Backend

This script creates an initial admin user for the HR Agent system using raw SQL.
"""

import sys
import os
from pathlib import Path
import uuid
import getpass
from typing import Optional
from sqlalchemy import create_engine, text
import logging

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleAdminCreator:
    """Simple admin creator using raw SQL"""
    
    def __init__(self):
        self.engine = None
    
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
            logger.info("✅ Database connection established")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise
    
    def check_user_exists(self, username: str, email: str) -> bool:
        """Check if user with username or email already exists"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT id FROM users WHERE username = :username OR email = :email"),
                    {"username": username, "email": email}
                )
                return result.fetchone() is not None
        except Exception as e:
            logger.error(f"❌ Error checking user existence: {e}")
            raise
    
    def create_admin_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str = "System Administrator",
        employee_id: str = None
    ) -> Optional[str]:
        """Create admin user using raw SQL"""
        try:
            # Check if user already exists
            if self.check_user_exists(username, email):
                logger.error(f"❌ User with username '{username}' or email '{email}' already exists")
                return None
            
            # Generate employee_id if not provided
            if not employee_id:
                employee_id = f"ADMIN{str(uuid.uuid4())[:8].upper()}"
            
            # Generate user ID
            user_id = str(uuid.uuid4())
            
            with self.engine.connect() as conn:
                # Create admin user using raw SQL
                hashed_password = get_password_hash(password)
                
                conn.execute(
                    text("""
                        INSERT INTO users (
                            id, username, email, full_name, hashed_password, 
                            role, is_superuser, is_verified, department, 
                            position, employee_id, created_at, updated_at, is_active
                        )
                        VALUES (
                            :id, :username, :email, :full_name, :hashed_password,
                            :role, :is_superuser, :is_verified, :department,
                            :position, :employee_id, NOW(), NOW(), :is_active
                        )
                    """),
                    {
                        "id": user_id,
                        "username": username,
                        "email": email,
                        "full_name": full_name,
                        "hashed_password": hashed_password,
                        "role": "ADMIN",
                        "is_superuser": True,
                        "is_verified": True,
                        "department": "IT",
                        "position": "System Administrator",
                        "employee_id": employee_id,
                        "is_active": True
                    }
                )
                
                conn.commit()
                
                logger.info("✅ Admin user created successfully!")
                logger.info(f"👤 Username: {username}")
                logger.info(f"📧 Email: {email}")
                logger.info(f"🔑 Password: {password}")
                logger.info(f"🆔 Employee ID: {employee_id}")
                logger.info(f"🔗 User ID: {user_id}")
                
                return user_id
                
        except Exception as e:
            logger.error(f"❌ Error creating admin user: {e}")
            raise
    
    def list_admin_users(self):
        """List all admin users using raw SQL"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT id, username, email, full_name, employee_id, created_at FROM users WHERE role = 'ADMIN'")
                )
                admin_users = result.fetchall()
                
                if not admin_users:
                    logger.info("ℹ️  No admin users found")
                    return
                
                logger.info(f"📋 Found {len(admin_users)} admin user(s):")
                for user in admin_users:
                    logger.info(f"  👤 {user.username} ({user.email}) - ID: {user.id}")
                    logger.info(f"     👨‍💼 Full Name: {user.full_name}")
                    logger.info(f"     🆔 Employee ID: {user.employee_id}")
                    logger.info(f"     📅 Created: {user.created_at}")
                    logger.info("     " + "-" * 50)
                    
        except Exception as e:
            logger.error(f"❌ Error listing admin users: {e}")
            raise
    
    def change_user_password(self, username: str, new_password: str):
        """Change user password using raw SQL"""
        try:
            with self.engine.connect() as conn:
                # Check if user exists
                result = conn.execute(
                    text("SELECT id FROM users WHERE username = :username"),
                    {"username": username}
                )
                user = result.fetchone()
                
                if not user:
                    logger.error(f"❌ User '{username}' not found")
                    return False
                
                # Update password
                hashed_password = get_password_hash(new_password)
                conn.execute(
                    text("UPDATE users SET hashed_password = :password, updated_at = NOW() WHERE username = :username"),
                    {"password": hashed_password, "username": username}
                )
                
                conn.commit()
                logger.info(f"✅ Password updated for user '{username}'")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error changing password: {e}")
            raise
    
    def cleanup(self):
        """Cleanup database connection"""
        if self.engine:
            self.engine.dispose()


def get_user_input():
    """Get user input for creating admin user"""
    print("\n🔧 Creating Admin User")
    print("=" * 50)
    
    username = input("Enter username: ").strip()
    if not username:
        print("❌ Username cannot be empty")
        return None
    
    email = input("Enter email: ").strip()
    if not email:
        print("❌ Email cannot be empty")
        return None
    
    password = getpass.getpass("Enter password: ")
    if not password:
        print("❌ Password cannot be empty")
        return None
    
    confirm_password = getpass.getpass("Confirm password: ")
    if password != confirm_password:
        print("❌ Passwords do not match")
        return None
    
    full_name = input("Enter full name (default: System Administrator): ").strip()
    if not full_name:
        full_name = "System Administrator"
    
    employee_id = input("Enter employee ID (optional): ").strip()
    if not employee_id:
        employee_id = None
    
    return {
        "username": username,
        "email": email,
        "password": password,
        "full_name": full_name,
        "employee_id": employee_id
    }


def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python create_admin_simple.py create          # Interactive creation")
        print("  python create_admin_simple.py create-quick    # Quick creation with defaults")
        print("  python create_admin_simple.py create-custom <username> <email> <password> <full_name>")
        print("  python create_admin_simple.py list            # List all admin users")
        print("  python create_admin_simple.py change-password <username>")
        sys.exit(1)
    
    command = sys.argv[1]
    creator = SimpleAdminCreator()
    
    try:
        creator.create_engine()
        
        if command == "create":
            user_data = get_user_input()
            if user_data:
                creator.create_admin_user(**user_data)
        
        elif command == "create-quick":
            creator.create_admin_user(
                username="admin",
                email="admin@hr-agent.com",
                password="admin123",
                full_name="System Administrator"
            )
        
        elif command == "create-custom":
            if len(sys.argv) < 6:
                print("❌ Usage: create-custom <username> <email> <password> <full_name>")
                sys.exit(1)
            
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
                print("❌ Usage: change-password <username>")
                sys.exit(1)
            
            username = sys.argv[2]
            new_password = getpass.getpass(f"Enter new password for '{username}': ")
            creator.change_user_password(username, new_password)
        
        else:
            print(f"❌ Unknown command: {command}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Command failed: {e}")
        sys.exit(1)
    finally:
        creator.cleanup()


if __name__ == "__main__":
    main()