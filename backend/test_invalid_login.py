#!/usr/bin/env python3
"""
Test invalid login credentials
"""
import requests
import json

def test_invalid_login():
    """Test login with invalid credentials"""
    url = "http://localhost:8000/api/v1/auth/login"
    
    # Test cases for invalid login
    test_cases = [
        {
            "name": "Wrong password",
            "data": {"username": "admin", "password": "wrongpassword"},
            "expected_status": 401
        },
        {
            "name": "Wrong username",
            "data": {"username": "wronguser", "password": "admin123"},
            "expected_status": 401
        },
        {
            "name": "Empty username",
            "data": {"username": "", "password": "admin123"},
            "expected_status": 422  # Validation error
        },
        {
            "name": "Empty password",
            "data": {"username": "admin", "password": ""},
            "expected_status": 422  # Validation error
        },
        {
            "name": "Both empty",
            "data": {"username": "", "password": ""},
            "expected_status": 422  # Validation error
        }
    ]
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    print("🔒 Testing invalid login scenarios...")
    print("=" * 60)
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Data: {test_case['data']}")
        
        try:
            response = requests.post(url, data=test_case['data'], headers=headers)
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Expected: {test_case['expected_status']}")
            
            if response.status_code == test_case['expected_status']:
                print("   ✅ PASS")
            else:
                print("   ❌ FAIL")
                all_passed = False
                
            # Show response content for debugging
            try:
                response_data = response.json()
                print(f"   Response: {response_data}")
            except:
                print(f"   Raw Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All invalid login tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False

if __name__ == "__main__":
    success = test_invalid_login()
    exit(0 if success else 1)