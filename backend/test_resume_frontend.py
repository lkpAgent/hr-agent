#!/usr/bin/env python3
"""
测试前端简历功能的完整流程
"""
import asyncio
import aiohttp
import json
import os
from pathlib import Path

async def login_and_get_token():
    """登录并获取token"""
    login_data = {
        'username': 'testuser2',
        'password': 'testpass123'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'http://localhost:8000/api/v1/auth/login',
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('access_token')
            else:
                error_text = await response.text()
                print(f"登录失败: {response.status} - {error_text}")
                return None

async def test_resume_frontend_flow():
    """测试前端简历功能流程"""
    print("=== 测试前端简历功能流程 ===")
    
    # 1. 登录获取token
    print("1. 登录获取token...")
    token = await login_and_get_token()
    if not token:
        print("❌ 登录失败，测试终止")
        return
    print("✅ 登录成功")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    async with aiohttp.ClientSession() as session:
        # 2. 测试获取简历历史（模拟前端fetchResumeList）
        print("\n2. 测试获取简历历史...")
        async with session.get(
            'http://localhost:8000/api/v1/resume-evaluation/history',
            headers=headers,
            params={'skip': 0, 'limit': 20}
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 获取简历历史成功")
                print(f"   总数: {data.get('total', 0)}")
                print(f"   当前页: {len(data.get('items', []))}")
                
                # 显示简历数据结构
                items = data.get('items', [])
                if items:
                    print("   简历数据示例:")
                    for i, item in enumerate(items[:2], 1):
                        print(f"     {i}. ID: {item.get('id')}")
                        print(f"        姓名: {item.get('candidate_name', 'N/A')}")
                        print(f"        职位: {item.get('candidate_position', 'N/A')}")
                        print(f"        分数: {item.get('total_score', 0)}")
                        print(f"        经验: {item.get('work_years', 'N/A')}")
                        print(f"        学历: {item.get('education_level', 'N/A')}")
                else:
                    print("   暂无简历数据")
            else:
                error_text = await response.text()
                print(f"❌ 获取简历历史失败: {response.status} - {error_text}")
        
        # 3. 测试获取支持的文件格式
        print("\n3. 测试获取支持的文件格式...")
        async with session.get(
            'http://localhost:8000/api/v1/resume-evaluation/supported-formats',
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 获取支持格式成功: {data}")
            else:
                error_text = await response.text()
                print(f"❌ 获取支持格式失败: {response.status} - {error_text}")
        
        # 4. 测试前端页面访问
        print("\n4. 测试前端页面访问...")
        try:
            # 测试简历筛选页面
            async with session.get('http://localhost:3001/recruitment/resume-screening') as response:
                if response.status == 200:
                    print("✅ 简历筛选页面访问成功")
                else:
                    print(f"❌ 简历筛选页面访问失败: {response.status}")
        except Exception as e:
            print(f"❌ 前端页面访问异常: {e}")
        
        # 5. 模拟前端数据转换逻辑
        print("\n5. 测试前端数据转换逻辑...")
        # 获取简历数据并模拟前端转换
        async with session.get(
            'http://localhost:8000/api/v1/resume-evaluation/history',
            headers=headers
        ) as response:
            if response.status == 200:
                backend_data = await response.json()
                
                # 模拟前端转换逻辑
                frontend_resumes = []
                for item in backend_data.get('items', []):
                    frontend_resume = {
                        'id': item.get('id'),
                        'name': item.get('candidate_name') or '未知',
                        'currentPosition': item.get('candidate_position') or '未知职位',
                        'experience': item.get('work_years') or '未知',
                        'education': item.get('education_level') or '未知',
                        'location': '未知',  # 后端暂无此字段
                        'age': item.get('candidate_age'),
                        'matchScore': round(item.get('total_score') or 0),
                        'skills': item.get('evaluation_metrics', {}).get('skills', []) if item.get('evaluation_metrics') else [],
                        'highlights': item.get('evaluation_metrics', {}).get('highlights', []) if item.get('evaluation_metrics') else [],
                        'avatar': '',
                        'workExperience': [],  # 后端暂无详细工作经历
                        'education_details': []  # 后端暂无详细教育背景
                    }
                    frontend_resumes.append(frontend_resume)
                
                print(f"✅ 前端数据转换成功，转换了 {len(frontend_resumes)} 条简历")
                if frontend_resumes:
                    print("   转换后的数据示例:")
                    sample = frontend_resumes[0]
                    print(f"     姓名: {sample['name']}")
                    print(f"     职位: {sample['currentPosition']}")
                    print(f"     匹配分数: {sample['matchScore']}")
                    print(f"     技能数量: {len(sample['skills'])}")
                    print(f"     亮点数量: {len(sample['highlights'])}")
    
    print("\n=== 前端简历功能测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_resume_frontend_flow())