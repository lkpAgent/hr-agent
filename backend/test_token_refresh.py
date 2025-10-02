#!/usr/bin/env python3
"""
Test token refresh endpoint
"""
import requests
import json
import time

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

def test_token_refresh(token):
    """Test token refresh endpoint"""
    url = "http://localhost:8000/api/v1/auth/refresh"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("🔄 Testing token refresh endpoint...")
    response = requests.post(url, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Content: {response.text}")
    
    if response.status_code == 200:
        token_data = response.json()
        new_token = token_data.get('access_token')
        print("✅ Token refresh successful!")
        print(f"New Token: {new_token[:20]}...")
        print(f"Token Type: {token_data.get('token_type')}")
        print(f"Expires In: {token_data.get('expires_in')} seconds")
        return new_token
    else:
        print("❌ Token refresh failed!")
        return None

def test_refresh_without_token():
    """Test refresh endpoint without token"""
    url = "http://localhost:8000/api/v1/auth/refresh"
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🚫 Testing refresh endpoint without token...")
    response = requests.post(url, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 401:
        print("✅ Correctly rejected request without token")
        error_data = response.json()
        print(f"Error message: {error_data}")
        return True
    else:
        print("❌ Should have rejected request without token")
        return False

def test_refresh_with_invalid_token():
    """Test refresh endpoint with invalid token"""
    url = "http://localhost:8000/api/v1/auth/refresh"
    headers = {
        "Authorization": "Bearer invalid_token_here",
        "Content-Type": "application/json"
    }
    
    print("🚫 Testing refresh endpoint with invalid token...")
    response = requests.post(url, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 401:
        print("✅ Correctly rejected request with invalid token")
        error_data = response.json()
        print(f"Error message: {error_data}")
        return True
    else:
        print("❌ Should have rejected request with invalid token")
        return False

def verify_new_token_works(token):
    """Verify that the new token works with /me endpoint"""
    url = "http://localhost:8000/api/v1/auth/me"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("✅ Verifying new token works with /me endpoint...")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"✅ New token works! User: {user_data.get('username')}")
        return True
    else:
        print(f"❌ New token doesn't work: {response.status_code}")
        return False

if __name__ == "__main__":
    print("🚀 Testing token refresh endpoint...")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Get fresh token and refresh it
    print("1. Testing token refresh with valid token...")
    token = get_fresh_token()
    if not token:
        print("💥 Failed to get initial token, exiting...")
        exit(1)
    
    print("-" * 40)
    new_token = test_token_refresh(token)
    if not new_token:
        all_passed = False
    else:
        # Verify new token works
        print("-" * 40)
        if not verify_new_token_works(new_token):
            all_passed = False
    
    print("\n" + "=" * 60)
    
    # Test 2: Test refresh without token
    print("2. Testing refresh endpoint without token...")
    if not test_refresh_without_token():
        all_passed = False
    
    print("\n" + "=" * 60)
    
    # Test 3: Test refresh with invalid token
    print("3. Testing refresh endpoint with invalid token...")
    if not test_refresh_with_invalid_token():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All token refresh tests passed!")
        exit(0)
    else:
        print("💥 Some tests failed!")
        exit(1)