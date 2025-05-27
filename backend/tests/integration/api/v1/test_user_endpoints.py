"""Integration tests for user management endpoints."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.service import create_access_token
from src.main import app
from src.users.domain.schemas import UserCreate
from src.users.infrastructure.repositories.user_repository import UserRepository

pytestmark = pytest.mark.asyncio


class TestUserEndpoints:
    """Test cases for user management endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession):
        """Create a test user and return user data and token."""
        repo = UserRepository(db_session)
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "Testpass123!",
            "first_name": "Test",
            "last_name": "User",
        }
        user = await repo.create(UserCreate(**user_data))
        token = create_access_token({"sub": str(user.id)})
        return {"user": user, "token": token}

    async def test_get_current_user_authenticated(self, client, test_user):
        """Test getting current user with valid token."""
        # Act
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user["user"].email
        assert data["username"] == test_user["user"].username
        assert "id" in data
        assert "hashed_password" not in data  # Sensitive data should be excluded

    async def test_get_current_user_unauthenticated(self, client):
        """Test getting current user without authentication."""
        # Act
        response = client.get("/api/v1/users/me")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_update_current_user(self, client, test_user):
        """Test updating current user's information."""
        # Arrange
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "username": "updateduser",
        }

        # Act
        response = client.patch(
            "/api/v1/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == update_data["first_name"]
        assert data["last_name"] == update_data["last_name"]
        assert data["username"] == update_data["username"]

    async def test_change_password_success(
        self, client, test_user, db_session: AsyncSession
    ):
        """Test changing password with correct current password."""
        # Arrange
        password_data = {
            "current_password": "Testpass123!",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        }

        # Act
        response = client.put(
            "/api/v1/users/me/password",
            json=password_data,
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Password updated successfully"

        # Verify the password was actually changed by trying to login with new password
        repo = UserRepository(db_session)
        user = await repo.get_by_email(test_user["user"].email)
        assert user.verify_password(password_data["new_password"])

    async def test_change_password_wrong_current_password(self, client, test_user):
        """Test changing password with incorrect current password."""
        # Arrange
        password_data = {
            "current_password": "WrongPassword123!",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        }

        # Act
        response = client.put(
            "/api/v1/users/me/password",
            json=password_data,
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Incorrect current password" in data["detail"]

    async def test_delete_current_user(
        self, client, test_user, db_session: AsyncSession
    ):
        """Test deleting the current user account."""
        # Act
        response = client.delete(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "User deleted successfully"

        # Verify user was actually deleted
        repo = UserRepository(db_session)
        user = await repo.get_by_id(test_user["user"].id)
        assert user is None
