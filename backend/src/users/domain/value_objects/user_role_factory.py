"""Factory for creating user roles with predefined permission sets.

This module provides the UserRoleFactory class which is responsible for creating
standardized user roles with predefined permission sets. It ensures consistency
in role definitions across the application.
"""

from enum import Enum
from typing import Type, TypeVar

from .policies import Permission
from .user_role import UserRole

T = TypeVar("T", bound="UserRoleFactory")


class RoleType(str, Enum):
    """Enumeration of role types with their display names."""

    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class UserRoleFactory:
    """Fluent interface for creating user roles with type safety.

    This class provides a type-safe way to create user roles using a fluent interface.
    Example usage:
        role = UserRoleFactory.get_role().user()  # Returns a standard user role
    """

    @classmethod
    def get_role(cls: Type[T]) -> T:
        """Start building a role with type safety.

        Returns:
            RoleFactory: A new instance of RoleFactory for method chaining

        Example:
            >>> role = UserRoleFactory.get_role().user()
            >>> role.name
            'user'
        """
        return cls()

    def user(self) -> UserRole:
        """Create a standard user role with basic permissions.

        Returns:
            UserRole: A UserRole instance with standard user permissions
        """
        return self._create_role(RoleType.USER)

    def admin(self) -> UserRole:
        """Create an admin role with full permissions.

        Returns:
            UserRole: A UserRole instance with admin permissions
        """
        return self._create_role(RoleType.ADMIN)

    def moderator(self) -> UserRole:
        """Create a moderator role with elevated permissions.

        Returns:
            UserRole: A UserRole instance with moderator permissions
        """
        return self._create_role(RoleType.MODERATOR)

    def create_default_role(self) -> UserRole:
        """Create a default role for a user.

        Returns:
            UserRole: A UserRole instance with default permissions
        """
        return self._create_role(RoleType.USER)

    def _create_role(self, role_type: RoleType) -> UserRole:
        """Internal method to create a role based on type.

        Args:
            role_type: The type of role to create

        Returns:
            UserRole: The created UserRole instance
        """
        role_creators = {
            RoleType.USER: self._create_user_role,
            RoleType.ADMIN: self._create_admin_role,
            RoleType.MODERATOR: self._create_moderator_role,
        }
        return role_creators[role_type]()

    @staticmethod
    def _create_user_role() -> UserRole:
        return UserRole(
            RoleType.USER,
            frozenset(
                {
                    Permission.READ_OWN,
                    Permission.UPDATE_OWN,
                    Permission.DELETE_OWN,
                }
            ),
        )

    @staticmethod
    def _create_admin_role() -> UserRole:
        return UserRole(
            RoleType.ADMIN,
            frozenset(Permission),  # All permissions
        )

    @staticmethod
    def _create_moderator_role() -> UserRole:
        return UserRole(
            RoleType.MODERATOR,
            frozenset(
                {
                    Permission.READ_ANY,
                    Permission.UPDATE_ANY,
                    Permission.DELETE_ANY,
                }
            ),
        )
