#!/usr/bin/env python3
"""
测试UserCreate schema
"""

from app.schemas.user import UserCreate

# 测试创建UserCreate对象
test_data = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "testpassword123",
    "full_name": "测试用户",
    "role": "hr"
}

try:
    user_create = UserCreate(**test_data)
    print("✅ UserCreate对象创建成功")
    print(f"Username: {user_create.username}")
    print(f"Email: {user_create.email}")
    print(f"Full name: {user_create.full_name}")
    print(f"Role: {user_create.role}")
    
    # 测试访问属性
    print(f"\n属性测试:")
    print(f"hasattr(user_create, 'username'): {hasattr(user_create, 'username')}")
    print(f"hasattr(user_create, 'email'): {hasattr(user_create, 'email')}")
    print(f"hasattr(user_create, 'password'): {hasattr(user_create, 'password')}")
    
except Exception as e:
    print(f"❌ 创建UserCreate对象失败: {e}")
    import traceback
    traceback.print_exc()