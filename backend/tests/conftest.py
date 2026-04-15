import pytest
import requests
import os

@pytest.fixture(scope="session")
def base_url():
    """Get base URL from environment."""
    url = os.environ.get('EXPO_PUBLIC_BACKEND_URL')
    if not url:
        pytest.fail("EXPO_PUBLIC_BACKEND_URL not set in environment")
    return url.rstrip('/')

@pytest.fixture(scope="session")
def api_client():
    """Shared requests session."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="session")
def auth_token(base_url, api_client):
    """Login and get auth token for authenticated requests."""
    response = api_client.post(
        f"{base_url}/api/auth/login",
        json={"email": "manager@darkstore.ai", "password": "darkstore2024"}
    )
    if response.status_code != 200:
        pytest.skip(f"Login failed: {response.status_code}")
    data = response.json()
    return data.get("token")

@pytest.fixture
def auth_headers(auth_token):
    """Headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}"}
