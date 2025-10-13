#!/usr/bin/env python3
"""
完整的前后端集成测试脚本
测试从登录到简历上传评估的完整流程
"""
import asyncio
import aiohttp
import json
import os

BASE_URL = "http://localhost:8000/api/v1"
FRONTEND_URL = "http://localhost:3001"

# 测试用户凭据
TEST_USERNAME = "testuser"
TEST_PASSWORD = "test123"

async def test_login():
    """测试登录功能"""
    print("=== 测试登录功能 ===")
    
    async with aiohttp.ClientSession() as session:
        login_data = {
            'username': TEST_USERNAME,
            'password': TEST_PASSWORD
        }
        
        async with session.post(
            f"{BASE_URL}/auth/login",
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        ) as response:
            if response.status == 200:
                result = await response.json()
                token = result.get("access_token")
                print(f"✅ 登录成功，Token: {token[:30]}...")
                return token
            else:
                error_text = await response.text()
                print(f"❌ 登录失败: {response.status} - {error_text}")
                return None

async def test_get_jds(token):
    """测试获取JD列表"""
    print("\n=== 测试获取JD列表 ===")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/hr-workflows/jd",
            headers=headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                # 检查返回的数据结构
                if isinstance(result, dict) and 'items' in result:
                    jds = result['items']
                elif isinstance(result, list):
                    jds = result
                else:
                    jds = []
                
                print(f"✅ 获取到 {len(jds)} 个JD")
                for jd in jds[:3]:  # 只显示前3个
                    print(f"  - {jd.get('title', 'N/A')} (ID: {jd.get('id', 'N/A')})")
                return jds
            else:
                error_text = await response.text()
                print(f"❌ 获取JD失败: {response.status} - {error_text}")
                return []

async def test_resume_upload(token, jd_id):
    """测试简历上传和评估"""
    print(f"\n=== 测试简历上传和评估 (JD: {jd_id}) ===")
    
    # 创建测试简历文件
    resume_content = """张三 - 高级前端开发工程师

联系方式：
电话：138-0000-0000
邮箱：zhangsan@example.com
地址：北京市朝阳区

教育背景：
2015-2019  北京理工大学  计算机科学与技术  本科

工作经验：
2019-2022  阿里巴巴  前端开发工程师
- 负责淘宝前端页面开发和维护
- 使用Vue.js、React开发大型电商项目
- 参与前端架构设计和性能优化

2022-至今  字节跳动  高级前端开发工程师
- 负责抖音前端核心功能开发
- 熟练使用TypeScript、Node.js
- 带领团队完成多个重要项目

技能专长：
- 前端框架：Vue.js、React、Angular
- 编程语言：JavaScript、TypeScript、HTML5、CSS3
- 工具链：Webpack、Vite、npm、yarn
- 版本控制：Git、SVN
- 其他：Node.js、Express、MongoDB

项目经验：
1. 电商平台前端重构项目
   - 使用Vue.js重构整个电商平台前端
   - 提升页面加载速度50%
   - 优化用户体验，提升转化率15%

2. 移动端H5应用开发
   - 开发多个移动端H5应用
   - 适配各种移动设备
   - 实现流畅的用户交互体验
"""
    
    # 保存到临时文件
    temp_file = "temp_resume.txt"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(resume_content)
    
    try:
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        data = aiohttp.FormData()
        data.add_field('job_description_id', jd_id)
        data.add_field('file', open(temp_file, 'rb'), filename='resume.txt', content_type='text/plain')
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/resume-evaluation/evaluate",
                headers=headers,
                data=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 简历上传成功")
                    
                    # 显示评估结果
                    if 'evaluation_metrics' in result:
                        metrics = result['evaluation_metrics']
                        print("\n📊 评估结果:")
                        
                        if isinstance(metrics, dict):
                            total_score = 0
                            count = 0
                            for key, value in metrics.items():
                                if isinstance(value, dict) and 'score' in value:
                                    score = value['score']
                                    reason = value.get('reason', '无')
                                    print(f"  {key}: {score}分 - {reason}")
                                    total_score += score
                                    count += 1
                            
                            if count > 0:
                                avg_score = total_score / count
                                print(f"\n平均分: {avg_score:.1f}分")
                        
                        # 显示其他信息
                        candidate_name = result.get('candidate_name', 'N/A')
                        match_score = result.get('match_score', 'N/A')
                        work_years = result.get('work_years', 'N/A')
                        
                        print(f"\n👤 候选人信息:")
                        print(f"  姓名: {candidate_name}")
                        print(f"  匹配分数: {match_score}")
                        print(f"  工作年限: {work_years}")
                    
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 简历上传失败: {response.status} - {error_text}")
                    return False
                    
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)

async def test_frontend_accessibility():
    """测试前端页面可访问性"""
    print(f"\n=== 测试前端页面可访问性 ===")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(FRONTEND_URL, timeout=5) as response:
                if response.status == 200:
                    print(f"✅ 前端页面可访问: {FRONTEND_URL}")
                    return True
                else:
                    print(f"❌ 前端页面访问失败: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 前端页面访问异常: {e}")
            return False

async def main():
    """主测试函数"""
    print("🚀 开始前后端集成测试")
    print("=" * 50)
    
    # 1. 测试前端可访问性
    frontend_ok = await test_frontend_accessibility()
    
    # 2. 测试登录
    token = await test_login()
    if not token:
        print("❌ 登录失败，无法继续测试")
        return
    
    # 3. 测试获取JD列表
    jds = await test_get_jds(token)
    if not jds:
        print("❌ 获取JD失败，无法继续测试")
        return
    
    # 4. 测试简历上传（使用第一个JD）
    first_jd = jds[0]
    jd_id = first_jd.get('id')
    if jd_id:
        upload_success = await test_resume_upload(token, jd_id)
    else:
        print("❌ 没有可用的JD ID")
        upload_success = False
    
    # 5. 总结测试结果
    print("\n" + "=" * 50)
    print("📋 测试结果总结:")
    print(f"  前端可访问性: {'✅ 通过' if frontend_ok else '❌ 失败'}")
    print(f"  用户登录: {'✅ 通过' if token else '❌ 失败'}")
    print(f"  JD列表获取: {'✅ 通过' if jds else '❌ 失败'}")
    print(f"  简历上传评估: {'✅ 通过' if upload_success else '❌ 失败'}")
    
    all_passed = frontend_ok and token and jds and upload_success
    print(f"\n🎯 整体测试结果: {'✅ 全部通过' if all_passed else '❌ 部分失败'}")
    
    if all_passed:
        print("\n🎉 恭喜！前后端集成测试全部通过！")
        print("💡 您现在可以:")
        print(f"   1. 访问前端页面: {FRONTEND_URL}")
        print(f"   2. 使用账号登录: {TEST_USERNAME}/{TEST_PASSWORD}")
        print("   3. 上传简历进行智能评估")
    else:
        print("\n⚠️  部分功能存在问题，请检查相关服务状态")

if __name__ == "__main__":
    asyncio.run(main())