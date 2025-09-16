#!/usr/bin/env python3
"""Simple script to test JWT token functionality with the auth service."""
import pytest
import requests
import json
import sys


def test_admin_login():
    """Test admin user login and JWT token retrieval."""
    base_url = "http://localhost:8004"

    # Test login with admin credentials
    login_data = {
        "username": "admin",
        "password": "admin"
    }

    response = requests.post(f"{base_url}/login", json=login_data)
    assert response.status_code == 200

    token_data = response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert "token_type" in token_data
    assert "expires_in" in token_data
    assert "user_id" in token_data
    assert "roles" in token_data

    # Test userinfo endpoint with the token
    access_token = token_data.get('access_token')
    assert access_token is not None

    headers = {"Authorization": f"Bearer {access_token}"}
    userinfo_response = requests.get(f"{base_url}/userinfo", headers=headers)
    assert userinfo_response.status_code == 200

    user_info = userinfo_response.json()
    assert "preferred_username" in user_info
    # Email might not be present for admin user in Keycloak
    # assert "email" in user_info
    assert "sub" in user_info  # User ID should always be present


def test_health_check():
    """Test health check endpoint."""
    base_url = "http://localhost:8004"

    response = requests.get(f"{base_url}/health")
    assert response.status_code == 200

    health_data = response.json()
    assert "status" in health_data
    assert "service" in health_data
