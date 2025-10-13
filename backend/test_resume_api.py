#!/usr/bin/env python3
"""
测试简历API功能
"""
import asyncio
import aiohttp
import json

async def login_and_get_token():
    """登录并获取token"""
    async with aiohttp.ClientSession() as session:
        # 尝试登录
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
                return data.get('access_token')
            else:
                print(f"登录失败: {response.status}")
                return None

async def test_resume_api():
    """测试简历API"""
    print("=== 测试简历API ===")
    
    # 先登录获取token
    token = await login_and_get_token()
    if not token:
        print("❌ 无法获取token，测试终止")
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # 测试获取简历历史
            print("1. 测试获取简历历史...")
            async with session.get(
                'http://localhost:8000/api/v1/resume-evaluation/history',
                headers=headers
            ) as response:
                print(f"状态码: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    print(f"✅ 获取简历历史成功，共 {data.get('total', 0)} 条记录")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取简历历史失败: {error_text}")
            
            # 测试获取支持的文件格式
            print("\n2. 测试获取支持的文件格式...")
            async with session.get(
                'http://localhost:8000/api/v1/resume-evaluation/supported-formats',
                headers=headers
            ) as response:
                print(f"状态码: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"支持的格式: {data}")
                    print("✅ 获取支持格式成功")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取支持格式失败: {error_text}")
                    
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_resume_api())