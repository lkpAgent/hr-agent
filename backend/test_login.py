#!/usr/bin/env python3
"""
Simple script to test login API
"""
import requests
import json

def test_login():
    """Test login endpoint"""
    url = "http://localhost:8000/api/v1/auth/login"
    
    # Test data
    data = {
        "username": "admin",
        "password": "admin123"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        print("Testing login endpoint...")
        print(f"URL: {url}")
        print(f"Data: {data}")
        
        response = requests.post(url, data=data, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Content: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Login successful!")
            print(f"Access Token: {token_data.get('access_token', 'N/A')[:50]}...")
            print(f"Token Type: {token_data.get('token_type', 'N/A')}")
            print(f"Expires In: {token_data.get('expires_in', 'N/A')} seconds")
            return token_data.get('access_token')
        else:
            print("❌ Login failed!")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during login test: {e}")
        return None

def test_health():
    """Test health endpoint"""
    url = "http://localhost:8000/api/v1/health"
    
    try:
        print("Testing health endpoint...")
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error during health test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting API tests...")
    print("=" * 50)
    
    # Test health first
    if test_health():
        print("✅ Health check passed")
    else:
        print("❌ Health check failed")
        exit(1)
    
    print("=" * 50)
    
    # Test login
    token = test_login()
    
    if token:
        print("=" * 50)
        print("🎉 All tests passed!")
    else:
        print("=" * 50)
        print("💥 Login test failed!")
        exit(1)