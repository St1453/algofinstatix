"""Test client utilities for making API requests."""

from typing import Any, Dict, Optional

from fastapi.testclient import TestClient


class TestAPIClient:
    """Extended test client with authentication support."""

    def __init__(self, client: TestClient, token: Optional[str] = None):
        """Initialize the test API client.

        Args:
            client: The FastAPI test client.
            token: Optional authentication token.
        """
        self.client = client
        self._token = token

    @property
    def headers(self) -> Dict[str, str]:
        """Get headers with authentication if token is set."""
        if self._token:
            return {"Authorization": f"Bearer {self._token}"}
        return {}

    def set_token(self, token: str) -> None:
        """Set the authentication token.

        Args:
            token: The JWT token for authentication.
        """
        self._token = token

    def clear_token(self) -> None:
        """Clear the authentication token."""
        self._token = None

    def get(self, url: str, **kwargs) -> Any:
        """Make a GET request.

        Args:
            url: The URL to request.
            **kwargs: Additional arguments to pass to the test client.

        Returns:
            The response object.
        """
        headers = {**self.headers, **kwargs.pop("headers", {})}
        return self.client.get(url, headers=headers, **kwargs)

    def post(self, url: str, json: Optional[Dict] = None, **kwargs) -> Any:
        """Make a POST request.

        Args:
            url: The URL to request.
            json: The JSON data to send.
            **kwargs: Additional arguments to pass to the test client.

        Returns:
            The response object.
        """
        headers = {**self.headers, **kwargs.pop("headers", {})}
        return self.client.post(url, json=json, headers=headers, **kwargs)

    def put(self, url: str, json: Optional[Dict] = None, **kwargs) -> Any:
        """Make a PUT request.

        Args:
            url: The URL to request.
            json: The JSON data to send.
            **kwargs: Additional arguments to pass to the test client.

        Returns:
            The response object.
        """
        headers = {**self.headers, **kwargs.pop("headers", {})}
        return self.client.put(url, json=json, headers=headers, **kwargs)

    def patch(self, url: str, json: Optional[Dict] = None, **kwargs) -> Any:
        """Make a PATCH request.

        Args:
            url: The URL to request.
            json: The JSON data to send.
            **kwargs: Additional arguments to pass to the test client.

        Returns:
            The response object.
        """
        headers = {**self.headers, **kwargs.pop("headers", {})}
        return self.client.patch(url, json=json, headers=headers, **kwargs)

    def delete(self, url: str, **kwargs) -> Any:
        """Make a DELETE request.

        Args:
            url: The URL to request.
            **kwargs: Additional arguments to pass to the test client.

        Returns:
            The response object.
        """
        headers = {**self.headers, **kwargs.pop("headers", {})}
        return self.client.delete(url, headers=headers, **kwargs)


def create_auth_client(
    client: TestClient, email: str, password: str, login_url: str = "/api/v1/auth/login"
) -> "TestAPIClient":
    """Create an authenticated test client.

    Args:
        client: The FastAPI test client.
        email: User email for authentication.
        password: User password for authentication.
        login_url: The login endpoint URL.

    Returns:
        An authenticated TestAPIClient instance.
    """
    # Create API client
    api_client = TestAPIClient(client)

    # Login to get token
    response = client.post(login_url, data={"username": email, "password": password})

    # Set the auth token
    if response.status_code == 200:
        token = response.json().get("access_token")
        if token:
            api_client.set_token(token)

    return api_client
