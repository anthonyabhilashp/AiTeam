#!/usr/bin/env python3
"""Simple script to test JWT token functionality with admin user."""
import requests
import json
import sys

def test_admin_login():
    """Test admin user login and JWT token retrieval."""
    base_url = "http://localhost:8004"

    print("🔐 Testing Admin User Login and JWT Token")
    print("=" * 50)

    # Test login with admin credentials
    login_data = {
        "username": "admin",
        "password": "admin"
    }

    try:
        print("📤 Attempting login with admin credentials...")
        response = requests.post(f"{base_url}/login", json=login_data, timeout=10)

        print(f"📥 Response Status: {response.status_code}")

        if response.status_code == 200:
            token_data = response.json()
            print("✅ Login successful!")
            print("\n🔑 JWT Token Details:")
            print(f"  Access Token: {token_data.get('access_token', 'N/A')[:50]}...")
            print(f"  Refresh Token: {token_data.get('refresh_token', 'N/A')[:50]}...")
            print(f"  Token Type: {token_data.get('token_type', 'N/A')}")
            print(f"  Expires In: {token_data.get('expires_in', 'N/A')} seconds")
            print(f"  User ID: {token_data.get('user_id', 'N/A')}")
            print(f"  Roles: {token_data.get('roles', [])}")

            # Test userinfo endpoint with the token
            access_token = token_data.get('access_token')
            if access_token:
                print("\n🔍 Testing User Info Endpoint...")
                headers = {"Authorization": f"Bearer {access_token}"}
                userinfo_response = requests.get(f"{base_url}/userinfo", headers=headers, timeout=10)

                if userinfo_response.status_code == 200:
                    user_info = userinfo_response.json()
                    print("✅ User info retrieved successfully!")
                    print(f"  Username: {user_info.get('preferred_username', 'N/A')}")
                    print(f"  Email: {user_info.get('email', 'N/A')}")
                    print(f"  Realm Roles: {user_info.get('realm_access', {}).get('roles', [])}")
                else:
                    print(f"❌ User info failed: {userinfo_response.status_code}")
                    print(f"Response: {userinfo_response.text}")

            return token_data
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Cannot connect to auth service")
        print("Make sure the auth service is running on http://localhost:8004")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_health_check():
    """Test health check endpoint."""
    base_url = "http://localhost:8004"

    print("\n🏥 Testing Health Check")
    print("=" * 30)

    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Health check passed!")
            print(f"  Status: {health_data.get('status', 'N/A')}")
            print(f"  Service: {health_data.get('service', 'N/A')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Auth Service JWT Token Test with Admin User")
    print("=" * 50)

    # Test health check first
    test_health_check()

    # Test admin login
    token_data = test_admin_login()

    if token_data:
        print("\n🎉 JWT Token test completed successfully!")
        print("The admin user can login and receive JWT tokens with proper roles.")
    else:
        print("\n❌ JWT Token test failed!")
        print("Check if the auth service is running and Keycloak is properly configured.")
        sys.exit(1)
