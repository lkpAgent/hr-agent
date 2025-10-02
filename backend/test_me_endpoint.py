#!/usr/bin/env python3
"""
Simple test for /me endpoint using a fresh token
"""
import requests
import json

def get_fresh_token():
    """Get a fresh access token"""
    url = "http://localhost:8000/api/v1/auth/login"
    data = {
        "username": "admin",
        "password": "admin123"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    print("🔑 Getting fresh access token...")
    response = requests.post(url, data=data, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        token = token_data.get('access_token')
        print(f"✅ Token obtained: {token[:20]}...")
        return token
    else:
        print(f"❌ Failed to get token: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_me_endpoint(token):
    """Test /me endpoint with token"""
    url = "http://localhost:8000/api/v1/auth/me"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("👤 Testing /me endpoint...")
    response = requests.get(url, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Content: {response.text}")
    
    if response.status_code == 200:
        user_data = response.json()
        print("✅ /me endpoint successful!")
        print(f"User ID: {user_data.get('id')}")
        print(f"Username: {user_data.get('username')}")
        print(f"Email: {user_data.get('email')}")
        print(f"Role: {user_data.get('role')}")
        return True
    else:
        print("❌ /me endpoint failed!")
        return False

if __name__ == "__main__":
    print("🚀 Testing /me endpoint...")
    print("=" * 50)
    
    # Get fresh token
    token = get_fresh_token()
    if not token:
        print("💥 Failed to get token, exiting...")
        exit(1)
    
    print("=" * 50)
    
    # Test /me endpoint
    success = test_me_endpoint(token)
    
    print("=" * 50)
    if success:
        print("🎉 Test passed!")
        exit(0)
    else:
        print("💥 Test failed!")
        exit(1)