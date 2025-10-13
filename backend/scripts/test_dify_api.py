#!/usr/bin/env python3
"""
Dify API测试脚本
用于测试与Dify工作流的连接和响应格式
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
load_dotenv()




def test_dify_api():
    """测试Dify API连接"""
    
    # 从环境变量获取配置
    dify_base_url = os.getenv('DIFY_BASE_URL')
    dify_api_key = os.getenv('DIFY_API_KEY')
    dify_user_id = os.getenv('DIFY_USER_ID', 'abc-123')
    
    if not dify_base_url or not dify_api_key:
        print("❌ 错误: 请在.env文件中配置DIFY_BASE_URL和DIFY_API_KEY")
        return False
    
    print(f"🔗 Dify Base URL: {dify_base_url}")
    print(f"🔑 API Key: {dify_api_key[:10]}...")
    print(f"👤 User ID: {dify_user_id}")
    print("-" * 50)
    
    # 构建请求数据
    request_data = {
        "inputs": {"type": 1},
        "query": "生成前端开发工程师的JD",
        "response_mode": "streaming",
        "conversation_id": "",
        "user": dify_user_id,
        "files": [
            {
                "type": "image",
                "transfer_method": "remote_url",
                "url": "https://cloud.dify.ai/logo/logo-site.png"
            }
        ]
    }
    
    # 构建请求头
    headers = {
        'Authorization': f'Bearer {dify_api_key}',
        'Content-Type': 'application/json'
    }
    
    print("📤 发送请求数据:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    print("-" * 50)
    
    try:
        # 发送请求
        url = f"{dify_base_url}/chat-messages"
        print(f"🌐 请求URL: {url}")
        
        response = requests.post(
            url,
            headers=headers,
            json=request_data,
            timeout=30,
            stream=True  # 支持流式响应
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📋 响应头: {dict(response.headers)}")
        print("-" * 50)
        
        if response.status_code == 200:
            print("✅ 请求成功!")
            print("📥 响应数据:")
            
            # 处理流式响应
            if response.headers.get('content-type', '').startswith('text/event-stream'):
                print("🔄 处理流式响应:")
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        print(f"  {line}")
                        # 尝试解析JSON数据
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                print(f"  解析数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                            except json.JSONDecodeError:
                                pass
            else:
                # 处理普通JSON响应
                try:
                    response_data = response.json()
                    print(json.dumps(response_data, indent=2, ensure_ascii=False))
                except json.JSONDecodeError:
                    print(response.text)
            
            return True
            
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

def test_dify_blocking_mode():
    """测试Dify API阻塞模式"""
    
    # 从环境变量获取配置
    dify_base_url = os.getenv('DIFY_BASE_URL')
    dify_api_key = os.getenv('DIFY_API_KEY')
    dify_user_id = os.getenv('DIFY_USER_ID', 'abc-123')
    
    print("\n" + "=" * 60)
    print("🔄 测试阻塞模式 (blocking)")
    print("=" * 60)
    
    # 构建请求数据 - 阻塞模式
    request_data = {
        "inputs": {"type": 1},
        "query": "生成前端开发工程师的JD",
        "response_mode": "blocking",  # 改为阻塞模式
        "conversation_id": "",
        "user": dify_user_id
    }
    
    # 构建请求头
    headers = {
        'Authorization': f'Bearer {dify_api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        url = f"{dify_base_url}/chat-messages"
        response = requests.post(
            url,
            headers=headers,
            json=request_data,
            timeout=60
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 阻塞模式请求成功!")
            response_data = response.json()
            print("📥 响应数据:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            return True
        else:
            print(f"❌ 阻塞模式请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 阻塞模式测试错误: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始测试Dify API")
    print("=" * 60)
    
    # 测试流式模式
    success1 = test_dify_api()
    
    # 测试阻塞模式
    success2 = test_dify_blocking_mode()
    
    print("\n" + "=" * 60)
    if success1 or success2:
        print("✅ 至少一种模式测试成功!")
    else:
        print("❌ 所有测试都失败了，请检查配置")
    print("=" * 60)