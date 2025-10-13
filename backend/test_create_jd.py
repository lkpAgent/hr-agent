#!/usr/bin/env python3
"""
测试脚本：创建JD数据
"""
import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8000/api/v1"

async def login():
    """登录获取token"""
    async with aiohttp.ClientSession() as session:
        login_data = {
            'username': 'testuser',
            'password': 'test123'
        }
        
        async with session.post(
            f"{BASE_URL}/auth/login",
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result.get("access_token")
            else:
                error_text = await response.text()
                print(f"登录失败: {response.status} - {error_text}")
                return None

async def create_jd(token, jd_data):
    """创建JD"""
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/hr-workflows/jd/save",
            headers=headers,
            json=jd_data
        ) as response:
            print(f"创建JD状态码: {response.status}")
            
            if response.status == 200:
                result = await response.json()
                jd_id = result.get("id")
                print(f"JD创建成功，ID: {jd_id}")
                print(f"JD标题: {jd_data['title']}")
                return jd_id
            else:
                error_text = await response.text()
                print(f"创建JD失败: {error_text}")
                return None

async def main():
    """主函数"""
    print("=== 创建测试JD数据 ===")
    
    # 登录
    token = await login()
    if not token:
        print("登录失败，无法继续")
        return
    
    print(f"登录成功，Token: {token[:20]}...")
    
    # 创建多个JD
    jd_list = [
        {
            "title": "高级前端开发工程师",
            "department": "技术部",
            "experience_level": "3-5年",
            "education": "本科及以上",
            "location": "北京",
            "salary_range": "25-35K",
            "job_type": "全职",
            "skills": ["Vue.js", "React", "JavaScript", "TypeScript", "Node.js"],
            "content": "负责前端架构设计和核心功能开发，参与产品需求分析和技术方案设计",
            "requirements": "熟悉Vue.js/React框架，有大型项目经验，了解前端工程化",
            "status": "published"
        },
        {
            "title": "Python后端开发工程师",
            "department": "技术部",
            "experience_level": "2-4年",
            "education": "本科及以上",
            "location": "上海",
            "salary_range": "20-30K",
            "job_type": "全职",
            "skills": ["Python", "FastAPI", "Django", "PostgreSQL", "Redis"],
            "content": "负责后端系统开发和维护，参与系统架构设计和性能优化",
            "requirements": "熟悉Python开发，有FastAPI或Django经验，了解数据库设计",
            "status": "published"
        },
        {
            "title": "全栈开发工程师",
            "department": "技术部",
            "experience_level": "3-5年",
            "education": "本科及以上",
            "location": "深圳",
            "salary_range": "22-32K",
            "job_type": "全职",
            "skills": ["Vue.js", "Python", "Node.js", "MySQL", "Docker"],
            "content": "负责前后端全栈开发，参与产品功能设计和技术选型",
            "requirements": "具备前后端开发能力，熟悉主流技术栈，有独立项目经验",
            "status": "published"
        }
    ]
    
    created_jds = []
    for jd_data in jd_list:
        jd_id = await create_jd(token, jd_data)
        if jd_id:
            created_jds.append({
                "id": jd_id,
                "title": jd_data["title"]
            })
    
    print(f"\n=== 创建完成，共创建 {len(created_jds)} 个JD ===")
    for jd in created_jds:
        print(f"ID: {jd['id']}, 标题: {jd['title']}")

if __name__ == "__main__":
    asyncio.run(main())