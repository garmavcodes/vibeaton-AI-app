"""Authentication endpoint tests."""
import pytest
import requests

class TestAuth:
    """Test authentication flows."""

    def test_health_check(self, base_url, api_client):
        """Test health endpoint is accessible."""
        response = api_client.get(f"{base_url}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        assert "timestamp" in data
        print("✓ Health check passed")

    def test_login_success(self, base_url, api_client):
        """Test successful login with correct credentials."""
        response = api_client.post(
            f"{base_url}/api/auth/login",
            json={"email": "manager@darkstore.ai", "password": "darkstore2024"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "manager@darkstore.ai"
        assert data["user"]["role"] == "manager"
        assert "id" in data["user"]
        assert "name" in data["user"]
        print(f"✓ Login successful for {data['user']['email']}")

    def test_login_invalid_credentials(self, base_url, api_client):
        """Test login fails with wrong password."""
        response = api_client.post(
            f"{base_url}/api/auth/login",
            json={"email": "manager@darkstore.ai", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        print("✓ Invalid credentials rejected correctly")

    def test_login_nonexistent_user(self, base_url, api_client):
        """Test login fails for non-existent user."""
        response = api_client.post(
            f"{base_url}/api/auth/login",
            json={"email": "nonexistent@test.com", "password": "test123"}
        )
        assert response.status_code == 401
        print("✓ Non-existent user rejected correctly")

    def test_get_current_user(self, base_url, api_client, auth_headers):
        """Test /auth/me endpoint returns current user."""
        response = api_client.get(
            f"{base_url}/api/auth/me",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "email" in data
        assert "id" in data
        assert "role" in data
        assert data["email"] == "manager@darkstore.ai"
        print(f"✓ Current user retrieved: {data['email']}")

    def test_logout(self, base_url, api_client, auth_headers):
        """Test logout endpoint."""
        response = api_client.post(
            f"{base_url}/api/auth/logout",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print("✓ Logout successful")
