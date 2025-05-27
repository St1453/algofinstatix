"""Integration tests for authentication endpoints."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.users.domain.schemas import UserCreate
from src.users.infrastructure.repositories.user_repository import UserRepository

pytestmark = pytest.mark.asyncio


class TestAuthEndpoints:
    """Test cases for authentication endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def user_data(self):
        """Sample user data for testing."""
        return {
            "email": "test@example.com",
            "username": "testuser",
            "password1": "Testpass123!",
            "password2": "Testpass123!",
            "first_name": "Test",
            "last_name": "User",
        }

    async def test_register_user_success(
        self, client, db_session: AsyncSession, user_data
    ):
        """Test successful user registration."""
        # Act
        response = client.post("/api/v1/auth/register", json=user_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "message" in data
        assert user_data["email"] in data["message"]

        # Verify user was created in the database
        repo = UserRepository(db_session)
        user = await repo.get_by_email(user_data["email"])
        assert user is not None
        assert user.email == user_data["email"]
        assert user.username == user_data["username"]

    async def test_register_duplicate_email(
        self, client, db_session: AsyncSession, user_data
    ):
        """Test registration with duplicate email."""
        # Arrange - Create a user first
        repo = UserRepository(db_session)
        await repo.create(
            UserCreate(**{**user_data, "password": user_data["password1"]})
        )

        # Act - Try to create user with same email
        response = client.post("/api/v1/auth/register", json=user_data)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "already registered" in data["detail"].lower()

    async def test_login_success(self, client, db_session: AsyncSession, user_data):
        """Test successful user login."""
        # Arrange - Create a user first
        repo = UserRepository(db_session)
        user = await repo.create(
            UserCreate(
                **{
                    "email": user_data["email"],
                    "username": user_data["username"],
                    "password": user_data["password1"],
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                }
            )
        )

        # Act - Login with correct credentials
        login_data = {
            "username": user_data["email"],
            "password": user_data["password1"],
        }
        response = client.post("/api/v1/auth/login", data=login_data)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(
        self, client, db_session: AsyncSession, user_data
    ):
        """Test login with invalid credentials."""
        # Act - Try to login with wrong password
        login_data = {"username": user_data["email"], "password": "wrongpassword"}
        response = client.post("/api/v1/auth/login", data=login_data)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Incorrect email or password" in data["detail"]

    async def test_get_current_user(self, client, db_session: AsyncSession, user_data):
        """Test getting current user with valid token."""
        # Arrange - Create a user and get token
        repo = UserRepository(db_session)
        user = await repo.create(
            UserCreate(
                **{
                    "email": user_data["email"],
                    "username": user_data["username"],
                    "password": user_data["password1"],
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                }
            )
        )

        # Get token
        login_data = {
            "username": user_data["email"],
            "password": user_data["password1"],
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]

        # Act - Get current user
        response = client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert "id" in data
