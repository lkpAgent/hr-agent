#!/usr/bin/env python3
"""
查看数据库中的用户信息
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.user_service import UserService

async def check_users():
    """查看数据库中的用户"""
    print("=== 查看数据库中的用户 ===")
    
    async for db in get_db():
        user_service = UserService(db)
        
        # 查找testuser
        user = await user_service.get_user_by_username("testuser")
        if user:
            print(f"找到用户: {user.username}")
            print(f"邮箱: {user.email}")
            print(f"全名: {user.full_name}")
            print(f"角色: {user.role}")
            print(f"是否验证: {user.is_verified}")
        else:
            print("未找到testuser用户")
            
        # 查找邮箱
        user_by_email = await user_service.get_user_by_email("testuser@example.com")
        if user_by_email:
            print(f"通过邮箱找到用户: {user_by_email.username}")
        else:
            print("未通过邮箱找到用户")
        
        break

if __name__ == "__main__":
    asyncio.run(check_users())