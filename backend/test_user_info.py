#!/usr/bin/env python3
"""
Test user info endpoint
"""
import requests
import json

def login_and_get_token():
    """Login and get access token"""
    url = "http://localhost:8000/api/v1/auth/login"
    data = {
        "username": "admin",
        "password": "admin123"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        print(f"Attempting login to: {url}")
        print(f"Data: {data}")
        response = requests.post(url, data=data, headers=headers)
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get('access_token')
        else:
            print(f"❌ Login failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Raw error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_user_info():
    """Test getting current user info"""
    print("👤 Testing user info endpoint...")
    print("=" * 50)
    
    # First login to get token
    print("1. Getting access token...")
    token = login_and_get_token()
    
    if not token:
        print("❌ Failed to get access token")
        return False
    
    print("✅ Access token obtained")
    
    # Test user info endpoint
    print("\n2. Testing /me endpoint...")
    url = "http://localhost:8000/api/v1/auth/me"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ User info retrieved successfully!")
            print(f"User Data:")
            print(f"  - ID: {user_data.get('id', 'N/A')}")
            print(f"  - Username: {user_data.get('username', 'N/A')}")
            print(f"  - Email: {user_data.get('email', 'N/A')}")
            print(f"  - Full Name: {user_data.get('full_name', 'N/A')}")
            print(f"  - Role: {user_data.get('role', 'N/A')}")
            print(f"  - Is Active: {user_data.get('is_active', 'N/A')}")
            print(f"  - Is Superuser: {user_data.get('is_superuser', 'N/A')}")
            print(f"  - Department: {user_data.get('department', 'N/A')}")
            print(f"  - Position: {user_data.get('position', 'N/A')}")
            print(f"  - Created At: {user_data.get('created_at', 'N/A')}")
            return True
        else:
            print("❌ Failed to get user info")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during user info test: {e}")
        return False

def test_user_info_without_token():
    """Test user info endpoint without token (should fail)"""
    print("\n3. Testing /me endpoint without token...")
    url = "http://localhost:8000/api/v1/auth/me"
    
    try:
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Correctly rejected request without token")
            try:
                error_data = response.json()
                print(f"Error message: {error_data}")
            except:
                print(f"Raw response: {response.text}")
            return True
        else:
            print("❌ Should have rejected request without token")
            return False
            
    except Exception as e:
        print(f"❌ Error during no-token test: {e}")
        return False

def test_user_info_with_invalid_token():
    """Test user info endpoint with invalid token (should fail)"""
    print("\n4. Testing /me endpoint with invalid token...")
    url = "http://localhost:8000/api/v1/auth/me"
    headers = {
        "Authorization": "Bearer invalid_token_here",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Correctly rejected request with invalid token")
            try:
                error_data = response.json()
                print(f"Error message: {error_data}")
            except:
                print(f"Raw response: {response.text}")
            return True
        else:
            print("❌ Should have rejected request with invalid token")
            return False
            
    except Exception as e:
        print(f"❌ Error during invalid token test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting user info API tests...")
    print("=" * 60)
    
    all_passed = True
    
    # Test with valid token
    if not test_user_info():
        all_passed = False
    
    # Test without token
    if not test_user_info_without_token():
        all_passed = False
    
    # Test with invalid token
    if not test_user_info_with_invalid_token():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All user info tests passed!")
        exit(0)
    else:
        print("💥 Some tests failed!")
        exit(1)