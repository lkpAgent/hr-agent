#!/usr/bin/env python3
"""
调试UserCreate schema的问题
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.schemas.user import UserCreate, UserBase
from app.models.user import UserRole

# 测试数据
test_data = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "testpassword123",
    "full_name": "测试用户",
    "role": "hr_specialist"
}

print("=== 调试UserCreate schema ===")
print(f"测试数据: {test_data}")

try:
    # 创建UserCreate对象
    user_create = UserCreate(**test_data)
    print(f"✅ 成功创建UserCreate对象")
    print(f"对象内容: {user_create}")
    print(f"对象字典: {user_create.model_dump()}")
    
    # 检查属性
    print(f"\n=== 检查属性 ===")
    print(f"username: {hasattr(user_create, 'username')} - {getattr(user_create, 'username', 'NOT FOUND')}")
    print(f"email: {hasattr(user_create, 'email')} - {getattr(user_create, 'email', 'NOT FOUND')}")
    print(f"password: {hasattr(user_create, 'password')} - {getattr(user_create, 'password', 'NOT FOUND')}")
    print(f"role: {hasattr(user_create, 'role')} - {getattr(user_create, 'role', 'NOT FOUND')}")
    
    # 检查字段定义
    print(f"\n=== 检查字段定义 ===")
    print(f"UserCreate字段: {list(user_create.model_fields.keys())}")
    print(f"UserBase字段: {list(UserBase.model_fields.keys())}")
    
except Exception as e:
    print(f"❌ 创建UserCreate对象失败: {e}")
    import traceback
    traceback.print_exc()