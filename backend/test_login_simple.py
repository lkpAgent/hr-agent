#!/usr/bin/env python3
"""
测试登录的简单脚本
"""
import asyncio
import aiohttp
import json

async def test_login():
    """测试不同的用户名密码组合"""
    print("=== 测试登录 ===")
    
    # 测试不同的用户名密码组合
    test_combinations = [
        {'username': 'testuser', 'password': 'testpass123'},
        {'username': 'testuser', 'password': 'password'},
        {'username': 'testuser', 'password': '123456'},
        {'username': 'admin', 'password': 'admin'},
        {'username': 'admin', 'password': 'admin123'},
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, login_data in enumerate(test_combinations, 1):
            print(f"\n--- 测试组合 {i}: {login_data['username']}/{login_data['password']} ---")
            
            try:
                async with session.post(
                    'http://localhost:8000/api/v1/auth/login',
                    data=login_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ 登录成功!")
                        print(f"Token: {result.get('access_token', 'N/A')[:50]}...")
                        return login_data  # 返回成功的组合
                    else:
                        error_text = await response.text()
                        print(f"❌ 登录失败: {response.status} - {error_text}")
                        
            except Exception as e:
                print(f"❌ 请求异常: {e}")
    
    print("\n所有登录组合都失败了")
    return None

if __name__ == "__main__":
    result = asyncio.run(test_login())
    if result:
        print(f"\n成功的登录组合: {result}")