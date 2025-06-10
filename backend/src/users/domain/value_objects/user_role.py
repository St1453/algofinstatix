"""UserRole value object for managing user roles and permissions.

This module defines the UserRole class that represents a user's role and its
associated permissions in the system. It provides methods to check permissions
and manage role-based access control.
"""

from dataclasses import dataclass
from typing import FrozenSet, TypeVar

from .policies import Permission

T = TypeVar('T', bound='UserRole')


@dataclass(frozen=True)
class UserRole:
    """Represents a user role with associated permissions.
    
    Roles are used to manage user access control and determine what actions
    a user can perform within the system. Each role has a name and a set of
    permissions that define what actions are allowed for users with that role.
    """
    name: str
    permissions: FrozenSet[Permission]

    def __post_init__(self) -> None:
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
            >>> from .policies import Permission
            >>> role = UserRole("user", frozenset({Permission.READ_OWN}))
            >>> role.has_permission(Permission.READ_OWN)
            True
        """
        return permission in self.permissions

    def has_any_permission(self, *permissions: Permission) -> bool:
        """Check if this role has any of the specified permissions.
        
        Args:
            *permissions: One or more permissions to check
            
        Returns:
            bool: True if the role has at least one of the specified permissions
            
        Example:
            >>> perms = frozenset({Permission.READ_OWN, Permission.UPDATE_OWN})
            >>> role = UserRole("user", perms)
            >>> role.has_any_permission(Permission.READ_OWN, Permission.READ_ANY)
            True
        """
        if not permissions:
            return False
        return any(self.has_permission(p) for p in permissions)

    def has_all_permissions(self, *permissions: Permission) -> bool:
        """Check if this role has all of the specified permissions.
        
        Args:
            *permissions: One or more permissions to check
            
        Returns:
            bool: True if the role has all of the specified permissions
            
        Example:
            >>> perms = frozenset({Permission.READ_OWN, Permission.UPDATE_OWN})
            >>> role = UserRole("user", perms)
            >>> role.has_all_permissions(Permission.READ_OWN, Permission.UPDATE_OWN)
            True
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
    
    def __str__(self) -> str:
        """String representation of the role."""
        return self.name
