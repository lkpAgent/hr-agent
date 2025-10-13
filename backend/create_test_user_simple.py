#!/usr/bin/env python3
"""
创建测试用户的简单脚本
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def create_test_user():
    """创建测试用户"""
    print("=== 创建测试用户 ===")
    
    async for db in get_db():
        try:
            # 检查用户是否已存在
            existing_user = await db.execute(
                text("SELECT * FROM users WHERE username = 'testuser'")
            )
            user = existing_user.fetchone()
            
            if user:
                print("用户 testuser 已存在，删除旧用户...")
                await db.execute(text("DELETE FROM users WHERE username = 'testuser'"))
                await db.commit()
            
            # 创建新用户
            hashed_password = get_password_hash("testpass123")
            
            new_user = User(
                username="testuser",
                email="test@example.com",
                full_name="Test User",
                hashed_password=hashed_password,
                role="admin",
                is_superuser=True,
                is_verified=True,
                is_active=True
            )
            
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            print(f"成功创建用户: {new_user.username}")
            print(f"用户ID: {new_user.id}")
            print(f"密码: testpass123")
            
        except Exception as e:
            print(f"创建用户失败: {e}")
            await db.rollback()
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(create_test_user())