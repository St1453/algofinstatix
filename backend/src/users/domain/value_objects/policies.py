"""Core permission definitions for the users domain.

This module defines the base permission flags that are used throughout the application
for access control and authorization.
"""

from enum import Flag, auto


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
