"""UserRole value object for managing user roles and permissions."""

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Type, TypeVar

from src.users.domain.entities.user import Permission

T = TypeVar("T", bound="UserRole")


class RoleType(str, Enum):
    """Enumeration of role types."""

    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


@dataclass(frozen=True)
class UserRole:
    """Value object representing a user role with permissions."""

    name: str
    permissions: FrozenSet[Permission]

    def has_permission(self, permission: Permission) -> bool:
        """Check if this role has the specified permission."""
        return permission in self.permissions

    def has_any_permission(self, *permissions: Permission) -> bool:
        """Check if this role has any of the specified permissions."""
        return any(p in self.permissions for p in permissions)

    def has_all_permissions(self, *permissions: Permission) -> bool:
        """Check if this role has all of the specified permissions."""
        return all(p in self.permissions for p in permissions)

    # Role creation methods
    @classmethod
    def create_user_role(cls: Type[T]) -> T:
        """Create a standard user role with basic permissions.

        Returns:
            UserRole: A new UserRole instance with standard user permissions

        Example:
            >>> user_role = UserRole.create_user_role()
        """
        return cls(
            name=RoleType.USER,
            permissions=frozenset(
                {
                    Permission.READ_OWN,
                    Permission.UPDATE_OWN,
                    Permission.DELETE_OWN,
                }
            ),
        )

    @classmethod
    def create_admin_role(cls: Type[T]) -> T:
        """Create an admin role with all permissions.

        Returns:
            UserRole: A new UserRole instance with all permissions

        Example:
            >>> admin_role = UserRole.create_admin_role()
        """
        return cls(name=RoleType.ADMIN, permissions=frozenset(iter(Permission)))

    @classmethod
    def create_moderator_role(cls: Type[T]) -> T:
        """Create a moderator role with limited admin permissions.

        Returns:
            UserRole: A new UserRole instance with moderator permissions

        Example:
            >>> mod_role = UserRole.create_moderator_role()
        """
        return cls(
            name=RoleType.MODERATOR,
            permissions=frozenset(
                {
                    Permission.READ_ANY,
                    Permission.UPDATE_ANY,
                    Permission.DELETE_ANY,
                }
            ),
        )

    @classmethod
    def from_name(cls: Type[T], name: str) -> T:
        """Create a role from a role name.

        Args:
            name: The name of the role to create (user, admin, moderator)

        Returns:
            UserRole: A new UserRole instance with the specified role

        Raises:
            ValueError: If the role name is invalid

        Example:
            >>> role = UserRole.from_name('admin')
        """
        name = name.lower()
        if name == RoleType.USER:
            return cls.create_user_role()
        elif name == RoleType.ADMIN:
            return cls.create_admin_role()
        elif name == RoleType.MODERATOR:
            return cls.create_moderator_role()
        raise ValueError(f"Unknown role name: {name}")

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UserRole):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)
