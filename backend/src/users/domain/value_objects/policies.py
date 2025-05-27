"""Core permission and role definitions for the users domain.

This module defines the base permission flags and the UserRole class that are used
throughout the application for access control and authorization.
"""

from dataclasses import dataclass
from enum import Flag, auto
from typing import FrozenSet


class Permission(Flag):
    """Base permissions that can be combined to define access levels.

    Permissions are designed to be combined using bitwise operations to create
    fine-grained access control. Each permission represents a specific action
    that can be performed in the system.

    Attributes:
        READ_OWN: Can view their own user data
        UPDATE_OWN: Can update their own user data
        DELETE_OWN: Can delete their own user account
        CREATE_ACCOUNT_FULL: Can create new user accounts (admin only)
        READ_ANY: Can view any user's data (admin only)
        UPDATE_ANY: Can update any user's data (admin only)
        DELETE_ANY: Can delete any user account (admin only)
    """

    # Base permissions (available to regular users)
    READ_OWN = auto()  # Can view their own data
    UPDATE_OWN = auto()  # Can update their own data
    DELETE_OWN = auto()  # Can delete their own account

    # Admin permissions (only for administrative users)
    CREATE_ACCOUNT_FULL = auto()  # Can create new users (admin)
    READ_ANY = auto()  # Can view any user's data (admin)
    UPDATE_ANY = auto()  # Can update any user's data (admin)
    DELETE_ANY = auto()  # Can delete any user (admin)


@dataclass(frozen=True)
class UserRole:
    """Represents a user role with associated permissions.

    Roles are used to manage user access control and determine what actions
    a user can perform within the system. Each role has a name and a set of
    permissions that define what actions are allowed for users with that role.

    Attributes:
        name: The name of the role (e.g., 'user', 'admin')
        permissions: A set of Permission flags that this role has access to
    """

    name: str
    permissions: FrozenSet[Permission]

    def __post_init__(self):
        """Validate the role after initialization."""
        if not self.name:
            raise ValueError("Role name cannot be empty")
        if not isinstance(self.permissions, (set, frozenset)):
            raise TypeError("Permissions must be a set or frozenset")

    def has_permission(self, permission: Permission) -> bool:
        """Check if this role has the specified permission.

        Args:
            permission: The permission to check against this role's permissions

        Returns:
            bool: True if this role has the permission, False otherwise

        Example:
            >>> role = UserRole("user", {Permission.READ_OWN})
            >>> role.has_permission(Permission.READ_OWN)
            True
            >>> role.has_permission(Permission.READ_ANY)
            False
        """
        return permission in self.permissions

    def has_any_permission(self, *permissions: Permission) -> bool:
        """Check if this role has any of the specified permissions.

        Args:
            *permissions: One or more permissions to check

        Returns:
            bool: True if the role has at least one of the permissions

        Example:
            >>> role = UserRole("user", {Permission.READ_OWN, Permission.UPDATE_OWN})
            >>> role.has_any_permission(Permission.READ_OWN, Permission.READ_ANY)
            True
        """
        if not permissions:
            return False
        return any(self.has_permission(p) for p in permissions)

    def has_all_permissions(self, *permissions: Permission) -> bool:
        """Check if this role has all of the specified permissions.

        This method ensures the role has every single permission specified.
        Returns True only if all permissions are present.

        Args:
            *permissions: One or more permissions to check

        Returns:
            bool: True if the role has all of the specified permissions

        Example:
            >>> role = UserRole("admin", {Permission.READ_OWN, Permission.UPDATE_OWN})
            >>> role.has_all_permissions(Permission.READ_OWN, Permission.UPDATE_OWN)
            True
            >>> role.has_all_permissions(Permission.READ_OWN, Permission.READ_ANY)
            False
        """
        if not permissions:
            return False
        return all(self.has_permission(p) for p in permissions)

    def can_grant_permission(self, permission: Permission) -> bool:
        """Check if this role can grant the specified permission to another role.

        By default, a role can only grant permissions that it has itself.

        Args:
            permission: The permission to check

        Returns:
            bool: True if this role can grant the permission
        """
        return self.has_permission(permission)

    def __eq__(self, other: object) -> bool:
        """Two roles are equal if they have the same name and permissions."""
        if not isinstance(other, UserRole):
            return False
        return self.name == other.name and self.permissions == other.permissions

    def __hash__(self) -> int:
        """Hash based on role name and permissions."""
        return hash((self.name, frozenset(self.permissions)))
