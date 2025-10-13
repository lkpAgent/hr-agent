#!/usr/bin/env python3
"""
创建测试用户脚本
"""

import asyncio
import aiohttp
import json

# API配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# 测试用户信息
TEST_USER = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "test12345",
    "full_name": "测试用户",
    "role": "hr_specialist"
}

async def create_test_user():
    """创建测试用户"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_BASE}/auth/register",
            json=TEST_USER
        ) as response:
            print(f"创建用户状态码: {response.status}")
            
            if response.status == 200:
                result = await response.json()
                print(f"用户创建成功: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return True
            else:
                text = await response.text()
                print(f"用户创建失败: {text}")
                return False

async def test_login():
    """测试登录"""
    async with aiohttp.ClientSession() as session:
        login_data = {
            "username": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
        
        async with session.post(
            f"{API_BASE}/auth/login",
            data=login_data
        ) as response:
            print(f"\n登录状态码: {response.status}")
            
            if response.status == 200:
                result = await response.json()
                print(f"登录成功，获得token: {result.get('access_token')[:50]}...")
                return True
            else:
                text = await response.text()
                print(f"登录失败: {text}")
                return False

async def main():
    """主函数"""
    print("开始创建测试用户...")
    
    # 创建用户
    user_created = await create_test_user()
    
    if user_created:
        # 测试登录
        await test_login()
    
    print("\n完成！")

if __name__ == "__main__":
    asyncio.run(main())