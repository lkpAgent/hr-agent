#!/usr/bin/env python3
"""
测试前端集成 - 模拟前端登录并测试简历API
"""
import asyncio
import aiohttp
import json

async def test_frontend_integration():
    """测试前端集成"""
    print("=== 测试前端集成 ===")
    
    # 1. 登录获取token
    print("\n1. 登录获取token...")
    async with aiohttp.ClientSession() as session:
        login_data = {
            'username': 'testuser2',
            'password': 'testpass123'
        }
        
        async with session.post(
            'http://localhost:8000/api/v1/auth/login',
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        ) as response:
            if response.status == 200:
                data = await response.json()
                token = data.get('access_token')
                print(f"✅ 登录成功，获得token: {token[:50]}...")
            else:
                print(f"❌ 登录失败: {response.status}")
                return
    
    # 2. 测试获取用户信息
    print("\n2. 测试获取用户信息...")
    headers = {'Authorization': f'Bearer {token}'}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            'http://localhost:8000/api/v1/auth/me',
            headers=headers
        ) as response:
            if response.status == 200:
                user_data = await response.json()
                print(f"✅ 获取用户信息成功: {user_data.get('username')}")
            else:
                print(f"❌ 获取用户信息失败: {response.status}")
    
    # 3. 测试简历API
    print("\n3. 测试简历API...")
    async with aiohttp.ClientSession() as session:
        # 获取简历历史
        async with session.get(
            'http://localhost:8000/api/v1/resume-evaluation/history',
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 获取简历历史成功，共 {data.get('total', 0)} 条记录")
                
                # 如果有简历数据，显示前几条
                items = data.get('items', [])
                if items:
                    print("前几条简历记录:")
                    for i, item in enumerate(items[:3], 1):
                        print(f"  {i}. {item.get('candidate_name', 'N/A')} - {item.get('position', 'N/A')}")
                else:
                    print("暂无简历数据")
            else:
                print(f"❌ 获取简历历史失败: {response.status}")
        
        # 获取支持的文件格式
        async with session.get(
            'http://localhost:8000/api/v1/resume-evaluation/supported-formats',
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 获取支持格式成功: {data.get('supported_extensions', [])}")
            else:
                print(f"❌ 获取支持格式失败: {response.status}")
    
    print("\n=== 前端集成测试完成 ===")
    print(f"Token可用于前端测试: {token}")

if __name__ == "__main__":
    asyncio.run(test_frontend_integration())