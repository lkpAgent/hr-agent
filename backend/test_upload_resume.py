#!/usr/bin/env python3
"""
测试上传简历数据
"""
import asyncio
import aiohttp
import json
import io

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

async def create_test_resume():
    """创建测试简历内容"""
    resume_content = """
张三
软件工程师

联系方式：
电话：138-0000-0000
邮箱：zhangsan@example.com
地址：北京市朝阳区

教育背景：
2018-2022  北京大学  计算机科学与技术  本科

工作经验：
2022-2024  阿里巴巴  Python后端开发工程师
- 负责电商平台后端API开发
- 使用Python、Django、MySQL、Redis等技术栈
- 参与微服务架构设计和实现
- 优化系统性能，提升接口响应速度50%

技能：
- 编程语言：Python、Java、JavaScript
- 框架：Django、Flask、Spring Boot、Vue.js
- 数据库：MySQL、PostgreSQL、Redis、MongoDB
- 工具：Git、Docker、Kubernetes、Jenkins

项目经验：
1. 电商平台后端系统
   - 技术栈：Python + Django + MySQL + Redis
   - 负责用户管理、订单处理、支付集成等模块
   - 日处理订单量10万+

2. 微服务架构改造
   - 将单体应用拆分为微服务架构
   - 使用Docker容器化部署
   - 提升系统可扩展性和维护性
"""
    return resume_content

async def get_test_jd_id():
    """获取测试用的JD ID"""
    # 使用刚创建的Python后端开发工程师JD ID
    return "64ac9184-b849-4f58-a0c9-c7b3b3a28bc5"

async def test_upload_resume():
    """测试上传简历"""
    print("=== 测试上传简历 ===")
    
    # 1. 登录获取token
    print("1. 登录获取token...")
    token = await login_and_get_token()
    if not token:
        print("❌ 登录失败，测试终止")
        return
    print("✅ 登录成功")
    
    # 2. 创建测试简历文件
    print("2. 创建测试简历...")
    resume_content = await create_test_resume()
    jd_id = await get_test_jd_id()
    
    # 3. 上传简历
    print("3. 上传简历...")
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    # 创建表单数据
    data = aiohttp.FormData()
    data.add_field('job_description_id', jd_id)
    data.add_field('conversation_id', '550e8400-e29b-41d4-a716-446655440001')  # 测试会话ID
    
    # 添加文件
    file_content = resume_content.encode('utf-8')
    data.add_field('file', 
                   io.BytesIO(file_content),
                   filename='张三_简历.txt',
                   content_type='text/plain')
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                'http://localhost:8000/api/v1/resume-evaluation/evaluate',
                headers=headers,
                data=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 简历上传成功")
                    print(f"   评价ID: {result.get('id')}")
                    print(f"   候选人: {result.get('name')}")
                    print(f"   职位: {result.get('position')}")
                    print(f"   总分: {result.get('total_score')}")
                    return result.get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 简历上传失败: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ 上传异常: {e}")
            return None

async def test_get_resume_list():
    """测试获取简历列表"""
    print("\n4. 测试获取简历列表...")
    
    token = await login_and_get_token()
    if not token:
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            'http://localhost:8000/api/v1/resume-evaluation/history',
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 获取简历列表成功")
                print(f"   总数: {data.get('total', 0)}")
                
                items = data.get('items', [])
                if items:
                    print("   简历列表:")
                    for i, item in enumerate(items, 1):
                        print(f"     {i}. {item.get('candidate_name')} - {item.get('candidate_position')} (分数: {item.get('total_score')})")
                else:
                    print("   暂无简历数据")
            else:
                error_text = await response.text()
                print(f"❌ 获取简历列表失败: {response.status} - {error_text}")

async def main():
    """主函数"""
    # 上传测试简历
    evaluation_id = await test_upload_resume()
    
    # 获取简历列表
    await test_get_resume_list()
    
    print("\n=== 测试完成 ===")
    if evaluation_id:
        print(f"成功创建了简历评价记录: {evaluation_id}")
        print("现在可以在前端页面查看简历列表了！")

if __name__ == "__main__":
    asyncio.run(main())