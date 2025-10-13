import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# 配置
dify_base_url = os.getenv('DIFY_BASE_URL')
dify_api_key = os.getenv('DIFY_API_KEY')
dify_user_id = os.getenv('DIFY_USER_ID')

print(f"Base URL: {dify_base_url}")
print(f"API Key: {dify_api_key[:10]}...")
print(f"User ID: {dify_user_id}")

# 请求数据
data = {
    "inputs": {"type": 1},
    "query": "生成前端开发工程师的JD",
    "response_mode": "blocking",
    "conversation_id": "",
    "user": dify_user_id
}

headers = {
    'Authorization': f'Bearer {dify_api_key}',
    'Content-Type': 'application/json'
}

url = f"{dify_base_url}/chat-messages"
print(f"Request URL: {url}")

try:
    response = requests.post(url, headers=headers, json=data, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")