"""Integration tests for user registration functionality."""

import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestUserRegistration:
    """Test cases for user registration."""

    async def test_register_user_success(
        self, test_client: AsyncClient, random_email: str, random_username: str
    ):
        """Test successful user registration."""
        # Arrange
        user_data = {
            "email": random_email,
            "username": random_username,
            "password1": "Testpass123!",
            "password2": "Testpass123!",
            "first_name": "Test",
            "last_name": "User",
        }

        # Act
        response = await test_client.post("/api/v1/auth/register", json=user_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == f"User {user_data['email']} registered successfully"

    async def test_register_duplicate_user(
        self, test_client: AsyncClient, random_email: str, random_username: str
    ):
        """Test registering with an existing email."""
        # Arrange
        user_data = {
            "email": random_email,
            "username": random_username,
            "password1": "Testpass123!",
            "password2": "Testpass123!",
            "first_name": "Test",
            "last_name": "User",
        }

        # Register user first time (should succeed)
        response = await test_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED

        # Try to register again with same email (should fail)
        response = await test_client.post("/api/v1/auth/register", json=user_data)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "already registered" in data["detail"].lower()

    async def test_register_invalid_email(
        self, test_client: AsyncClient, random_username: str
    ):
        """Test registration with invalid email format."""
        # Arrange
        user_data = {
            "email": "invalid-email",
            "username": random_username,
            "password1": "Testpass123!",
            "password2": "Testpass123!",
            "first_name": "Test",
            "last_name": "User",
        }

        # Act
        response = await test_client.post("/api/v1/auth/register", json=user_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "value is not a valid email address" in str(data).lower()

    async def test_register_password_mismatch(
        self, test_client: AsyncClient, random_email: str, random_username: str
    ):
        """Test registration with mismatched passwords."""
        # Arrange
        user_data = {
            "email": random_email,
            "username": random_username,
            "password1": "Testpass123!",
            "password2": "DifferentPass123!",
            "first_name": "Test",
            "last_name": "User",
        }

        # Act
        response = await test_client.post("/api/v1/auth/register", json=user_data)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "passwords do not match" in data["detail"].lower()

    async def test_register_missing_required_fields(
        self, test_client: AsyncClient, random_email: str
    ):
        """Test registration with missing required fields."""
        # Test missing email
        user_data = {
            "username": "testuser",
            "password1": "Testpass123!",
            "password2": "Testpass123!",
        }
        response = await test_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test missing password
        user_data = {"email": random_email, "username": "testuser"}
        response = await test_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
