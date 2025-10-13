#!/usr/bin/env python3
"""
测试前端页面状态
"""
import asyncio
import aiohttp

async def test_frontend_status():
    """测试前端页面是否正常加载"""
    print("=== 测试前端页面状态 ===\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 测试前端首页
            print("📱 测试前端首页...")
            async with session.get('http://localhost:3001') as response:
                print(f"状态码: {response.status}")
                if response.status == 200:
                    content = await response.text()
                    if 'HR Agent' in content:
                        print("✅ 前端首页加载成功")
                    else:
                        print("⚠️ 前端首页内容异常")
                else:
                    print(f"❌ 前端首页加载失败: {response.status}")
            
            # 测试简历筛选页面
            print("\n📋 测试简历筛选页面...")
            async with session.get('http://localhost:3001/recruitment/resume-screening') as response:
                print(f"状态码: {response.status}")
                if response.status == 200:
                    print("✅ 简历筛选页面可访问")
                else:
                    print(f"❌ 简历筛选页面访问失败: {response.status}")
                    
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_frontend_status())