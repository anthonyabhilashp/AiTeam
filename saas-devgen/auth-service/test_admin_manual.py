#!/usr/bin/env python3
"""Manual test script for admin user functionality."""
import requests
import json
import sys
import os

# Configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8004")

def test_admin_login():
    """Test admin user login via auth service."""
    print("🔐 Testing Admin User Login")
    print("=" * 40)

    # Test login with admin credentials
    login_data = {
        "username": "admin",
        "password": "admin"
    }

    try:
        print(f"📡 Attempting login to {AUTH_SERVICE_URL}/login")
        response = requests.post(f"{AUTH_SERVICE_URL}/login", json=login_data, timeout=10)

        print(f"📊 Response Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"👤 User ID: {data.get('user_id', 'N/A')}")
            print(f"🔑 Access Token: {data.get('access_token', 'N/A')[:50]}...")
            print(f"🔄 Refresh Token: {data.get('refresh_token', 'N/A')[:50]}...")
            print(f"⏰ Expires In: {data.get('expires_in', 'N/A')} seconds")
            print(f"👥 Roles: {data.get('roles', [])}")

            # Test token validation
            access_token = data.get('access_token')
            if access_token:
                test_token_validation(access_token)

        else:
            print(f"❌ Login failed: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("💡 Make sure auth-service is running on port 8004")
        return False

    return True

def test_token_validation(access_token):
    """Test token validation."""
    print("\n🔍 Testing Token Validation")
    print("-" * 30)

    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{AUTH_SERVICE_URL}/userinfo", headers=headers, timeout=10)

        print(f"📊 Userinfo Response Status: {response.status_code}")

        if response.status_code == 200:
            user_data = response.json()
            print("✅ Token validation successful!")
            print(f"👤 Username: {user_data.get('preferred_username', 'N/A')}")
            print(f"📧 Email: {user_data.get('email', 'N/A')}")
            print(f"👥 Roles: {user_data.get('realm_access', {}).get('roles', [])}")
        else:
            print(f"❌ Token validation failed: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")

def test_keycloak_direct_login():
    """Test direct login to Keycloak."""
    print("\n🔑 Testing Direct Keycloak Login")
    print("-" * 35)

    try:
        # Keycloak token endpoint
        token_url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"

        data = {
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": "admin",
            "password": "admin"
        }

        print(f"📡 Attempting direct Keycloak login to {token_url}")
        response = requests.post(token_url, data=data, timeout=10)

        print(f"📊 Response Status: {response.status_code}")

        if response.status_code == 200:
            token_data = response.json()
            print("✅ Direct Keycloak login successful!")
            print(f"🔑 Access Token: {token_data.get('access_token', 'N/A')[:50]}...")
            print(f"⏰ Expires In: {token_data.get('expires_in', 'N/A')} seconds")
        else:
            print(f"❌ Direct Keycloak login failed: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("💡 Make sure Keycloak is running on port 8080")

def main():
    """Main test function."""
    print("🚀 Admin User Manual Test")
    print("=" * 50)
    print(f"🔗 Keycloak URL: {KEYCLOAK_URL}")
    print(f"🔗 Auth Service URL: {AUTH_SERVICE_URL}")
    print()

    # Test 1: Direct Keycloak login
    test_keycloak_direct_login()

    # Test 2: Auth service login
    success = test_admin_login()

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests completed successfully!")
        print("💡 Admin user is working correctly")
    else:
        print("⚠️  Some tests failed - check service status")
        print("💡 Make sure both Keycloak and auth-service are running")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
