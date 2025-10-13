#!/usr/bin/env python3
"""
测试简历上传API
"""
import asyncio
import aiohttp
import json
import os

async def test_resume_upload():
    """测试简历上传功能"""
    print("=== 测试简历上传API ===")
    
    # 使用提供的token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2NjNjM2EzMi01OTZjLTRmZWMtOTU1ZS02ZWFjZTg2ZWIyODEiLCJleHAiOjE3NTk4MjU0NzN9.YzqHaCJDnlBScHZmIBERhSr_iaxrGc4ZwPYeC7vYp9g"
    
    # JD ID (使用刚创建的高级前端开发工程师JD)
    job_description_id = "a7c88600-b8a3-4b54-9913-aea010f00183"
    
    # 简历文件路径
    resume_file_path = "test_resume.txt"
    
    if not os.path.exists(resume_file_path):
        print(f"❌ 简历文件不存在: {resume_file_path}")
        return
    
    async with aiohttp.ClientSession() as session:
        try:
            # 准备文件上传
            with open(resume_file_path, 'rb') as file:
                data = aiohttp.FormData()
                data.add_field('file', file, filename='test_resume.txt', content_type='text/plain')
                data.add_field('job_description_id', job_description_id)
                
                headers = {
                    'Authorization': f'Bearer {token}'
                }
                
                print(f"上传简历文件: {resume_file_path}")
                print(f"JD ID: {job_description_id}")
                print("发送请求...")
                
                async with session.post(
                    'http://localhost:8000/api/v1/resume-evaluation/evaluate',
                    data=data,
                    headers=headers
                ) as response:
                    print(f"响应状态码: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print("✅ 简历上传和评价成功!")
                        print(f"完整响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
                        
                        print(f"简历ID: {result.get('resume_id', 'N/A')}")
                        print(f"候选人姓名: {result.get('candidate_name', 'N/A')}")
                        print(f"匹配分数: {result.get('match_score', 'N/A')}")
                        print(f"工作年限: {result.get('work_experience', 'N/A')}")
                        print(f"教育背景: {result.get('education', 'N/A')}")
                        
                        # 显示评估指标
                        if 'evaluation_metrics' in result:
                            metrics = result['evaluation_metrics']
                            print(f"\n评估指标类型: {type(metrics)}")
                            print(f"评估指标内容: {metrics}")
                            if isinstance(metrics, dict):
                                for key, value in metrics.items():
                                    print(f"  {key}: {value}")
                            elif isinstance(metrics, list):
                                for i, item in enumerate(metrics):
                                    print(f"  {i}: {item}")
                        
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ 上传失败: {response.status}")
                        print(f"错误信息: {error_text}")
                        return False
                        
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_resume_upload())
    if success:
        print("\n🎉 简历上传测试成功!")
    else:
        print("\n💥 简历上传测试失败!")