#!/usr/bin/env python3
"""
检查简历数据结构
"""
import asyncio
import aiohttp
import json

async def check_resume_data():
    # 1. 登录获取token
    login_data = {
        "username": "testuser2",
        "password": "testpass123"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/api/v1/auth/login",
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        ) as response:
            if response.status == 200:
                login_result = await response.json()
                token = login_result.get("access_token")
                print("✅ 登录成功")
            else:
                print("❌ 登录失败")
                return
        
        # 2. 获取简历数据
        headers = {"Authorization": f"Bearer {token}"}
        async with session.get(
            "http://localhost:8000/api/v1/resume-evaluation/history",
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 获取简历数据成功")
                print(f"总数: {data.get('total', 0)}")
                
                if data.get('items'):
                    print("\n=== 完整的简历数据结构 ===")
                    for i, item in enumerate(data['items']):
                        print(f"\n简历 {i+1}:")
                        print(json.dumps(item, indent=2, ensure_ascii=False))
                        
                        # 特别检查resume_content字段
                        if 'resume_content' in item:
                            print(f"\n简历内容字段存在，长度: {len(item['resume_content'])}")
                            print(f"内容预览: {item['resume_content'][:200]}...")
                        else:
                            print("\n❌ 未找到resume_content字段")
                            print("可用字段:", list(item.keys()))
                else:
                    print("❌ 没有简历数据")
            else:
                print(f"❌ 获取简历数据失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(check_resume_data())