#!/usr/bin/env python3
"""
简历评价API测试脚本
"""

import asyncio
import aiohttp
import json
import os
from pathlib import Path

# API配置
BASE_URL = "http://localhost:8000/api/v1"

# 测试用户凭据（需要先登录获取token）
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test123"

async def login_and_get_token():
    """登录并获取访问令牌"""
    async with aiohttp.ClientSession() as session:
        login_data = {
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        async with session.post(
            f"{BASE_URL}/auth/login",
            data=login_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result.get("access_token")
            else:
                print(f"登录失败: {response.status}")
                text = await response.text()
                print(f"错误信息: {text}")
                return None

async def test_supported_formats(token):
    """测试获取支持的文件格式"""
    print("\n=== 测试支持的文件格式 ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/resume-evaluation/supported-formats", headers=headers) as response:
            print(f"状态码: {response.status}")
            
            if response.status == 200:
                data = await response.json()
                print(f"支持的格式: {data}")
                return True
            else:
                error_text = await response.text()
                print(f"错误: {error_text}")
                return False

async def create_test_jd(token):
    """创建测试用的JD"""
    print("\n=== 创建测试JD ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    jd_data = {
        "title": "Python后端开发工程师",
        "department": "技术部",
        "experience_level": "3-5年",
        "education": "本科及以上",
        "location": "北京",
        "salary_range": "20-30K",
        "job_type": "全职",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "content": "负责后端系统开发和维护，参与系统架构设计",
        "requirements": "熟悉Python开发，有FastAPI或Django经验，了解数据库设计",
        "status": "published"
    }
    
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
                return jd_id
            else:
                error_text = await response.text()
                print(f"创建JD失败: {error_text}")
                return None

async def test_resume_evaluation(token, jd_id):
    """测试简历评价功能"""
    if not jd_id:
        print("没有可用的JD ID，跳过简历评价测试")
        return

    print("\n=== 测试简历评价 ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 创建测试简历文件
    test_resume_content = """
    张三
    软件工程师
    
    联系方式：
    电话：138-0000-0000
    邮箱：zhangsan@example.com
    
    教育背景：
    2018-2022 北京大学 计算机科学与技术 本科
    
    工作经验：
    2022-2024 阿里巴巴 软件工程师
    - 负责电商平台后端开发
    - 使用Java、Spring Boot、MySQL等技术
    - 参与微服务架构设计和实现
    
    技能：
    - 编程语言：Java、Python、JavaScript
    - 框架：Spring Boot、Django、React
    - 数据库：MySQL、Redis、MongoDB
    - 工具：Git、Docker、Kubernetes
    
    项目经验：
    1. 电商平台订单系统
       - 使用Spring Boot开发订单管理系统
       - 实现高并发订单处理
       - 集成支付宝、微信支付
    
    2. 用户推荐系统
       - 基于协同过滤算法实现商品推荐
       - 使用Python和机器学习技术
       - 提升用户转化率15%
    """
    
    # 保存为临时文件
    temp_file = Path("temp_resume.txt")
    temp_file.write_text(test_resume_content, encoding='utf-8')
    
    try:
        async with aiohttp.ClientSession() as session:
            # 准备文件上传
            data = aiohttp.FormData()
            data.add_field('file', 
                          open(temp_file, 'rb'),
                          filename='resume.txt',
                          content_type='text/plain')
            data.add_field('job_description_id', str(jd_id))
            
            async with session.post(
                    f"{BASE_URL}/resume-evaluation/evaluate",
                headers=headers,
                data=data
            ) as response:
                print(f"状态码: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"评价结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    return True
                else:
                    text = await response.text()
                    print(f"错误: {text}")
                    return False
                    
    finally:
        # 清理临时文件
        if temp_file.exists():
            try:
                temp_file.unlink()
            except (OSError, PermissionError):
                pass  # 忽略文件清理错误

async def test_evaluation_history(token):
    """测试获取评价历史"""
    print("\n=== 测试评价历史 ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/resume-evaluation/history",
            headers=headers
        ) as response:
            print(f"状态码: {response.status}")
            
            if response.status == 200:
                result = await response.json()
                print(f"评价历史: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return True
            else:
                text = await response.text()
                print(f"错误: {text}")
                return False

async def main():
    """主测试函数"""
    print("开始测试简历评价API...")
    
    # 获取token
    token = await login_and_get_token()
    if not token:
        print("无法获取访问令牌，测试终止")
        return
    
    # 测试各个接口
    await test_supported_formats(token)
    await test_evaluation_history(token)
    
    # 创建测试JD并进行简历评价
    jd_id = await create_test_jd(token)
    await test_resume_evaluation(token, jd_id)
    
    print("\n测试完成！")

if __name__ == "__main__":
    asyncio.run(main())