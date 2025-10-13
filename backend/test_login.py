#!/usr/bin/env python3
"""
测试登录脚本
"""

import asyncio
import aiohttp
import json

# API配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

async def test_login():
    """测试登录"""
    async with aiohttp.ClientSession() as session:
        login_data = {
        "username": "test@example.com",  # 使用邮箱作为用户名
        "password": "test123"
    }
        
        async with session.post(
            f"{API_BASE}/auth/login",
            data=login_data
        ) as response:
            print(f"登录状态码: {response.status}")
            
            if response.status == 200:
                result = await response.json()
                print(f"登录成功！")
                print(f"Token: {result.get('access_token')[:50]}...")
                print(f"Token类型: {result.get('token_type')}")
                print(f"过期时间: {result.get('expires_in')}秒")
                return result.get('access_token')
            else:
                text = await response.text()
                print(f"登录失败: {text}")
                return None

async def main():
    """主函数"""
    print("测试登录...")
    token = await test_login()
    
    if token:
        print("\n✅ 登录测试成功！")
    else:
        print("\n❌ 登录测试失败！")

if __name__ == "__main__":
    asyncio.run(main())