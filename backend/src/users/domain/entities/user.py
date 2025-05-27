from __future__ import annotations

from dataclasses import dataclass, field
from dataclasses import replace as dataclass_replace
from datetime import datetime, timezone
from typing import ClassVar, FrozenSet, Optional

from src.users.domain.value_objects import Email, HashedPassword, UserStatus
from src.users.domain.value_objects.policies import Permission, UserRole
from src.users.domain.value_objects.user_role_factory import UserRoleFactory


@dataclass(frozen=True)
class User:
    """User domain entity representing a user in the system.

    This model encapsulates all user-related data and business rules.
    It's an immutable value object that represents a consistent user state.

    Attributes:
        id: Unique identifier (auto-generated if not provided)
        email: User's email address (must be unique)
        username: Unique username (optional)
        first_name: User's first name
        last_name: User's last name
        hashed_password: The hashed password
        status: User's account status (enabled, verified, locked, etc.)
        roles: User's roles (e.g., 'user', 'admin')
        bio: User's bio/description (optional)
        profile_picture: URL to the user's profile picture (optional)
        created_at: Timestamp when the user was created
        updated_at: Timestamp when the user was last updated
        deleted_at: Timestamp when the user was deleted (optional)
        mfa_enabled: Whether MFA is enabled for the user
        mfa_secret: MFA secret key (encrypted)
        password_reset_token: Token for password reset (encrypted)
        password_reset_token_expires: Expiration time for password reset token
    """

    # Core Identity
    id: str
    email: "Email"
    username: Optional[str] = None
    first_name: str
    last_name: str

    # Authentication
    hashed_password: HashedPassword
    status: "UserStatus" = field(default_factory=UserStatus)
    roles: FrozenSet[UserRole] = field(
        default_factory=lambda: frozenset({UserRoleFactory.user()})
    )

    # Profile
    bio: Optional[str] = None
    profile_picture: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

    # Security
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    password_reset_token: Optional[str] = None
    password_reset_token_expires: Optional[datetime] = None

    # Constants
    PASSWORD_EXPIRY_DAYS: ClassVar[int] = 90  # Default password expiry period

    def __post_init__(self) -> None:
        """Validate the user entity after initialization."""
        if not isinstance(self.status, UserStatus):
            raise ValueError("status must be an instance of UserStatus")
        if not all(
            hasattr(role, "name") and hasattr(role, "permissions")
            for role in self.roles
        ):
            raise ValueError("All roles must have 'name' and 'permissions' attributes")
        if not isinstance(self.email, Email):
            raise ValueError("email must be an instance of Email")
        if not isinstance(self.hashed_password, HashedPassword):
            raise ValueError("hashed_password must be an instance of HashedPassword")

    @property
    def full_name(self) -> str:
        """Get the user's full name.

        Returns:
            str: The concatenated first and last name

        Example:
            >>> user = User(..., first_name="John", last_name="Doe")
            >>> user.full_name
            'John Doe'
        """
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def has_role(self, role_name: str) -> bool:
        """Check if the user has a role with the specified name.

        Args:
            role_name: The name of the role to check for

        Returns:
            bool: True if the user has a role with the specified name

        Example:
            >>> user = User(..., roles=frozenset({UserRoleFactory.user()}))
            >>> user.has_role('user')
            True
            >>> user.has_role('admin')
            False
        """
        return any(role.name == role_name for role in self.roles)

    def has_permission(self, permission: Permission) -> bool:
        """Check if the user has the specified permission.

        A user has a permission if any of their roles have that permission.

        Args:
            permission: The permission to check

        Returns:
            bool: True if the user has the permission, False otherwise

        Example:
            >>> user = User(..., roles=frozenset({UserRoleFactory.user()}))
            >>> user.has_permission(Permission.READ_OWN)
            True
        """
        return any(role.has_permission(permission) for role in self.roles)

    def has_any_permission(self, *permissions: Permission) -> bool:
        """Check if the user has any of the specified permissions.

        Args:
            *permissions: One or more permissions to check

        Returns:
            bool: True if the user has at least one of the permissions

        Example:
            >>> user = User(..., roles=frozenset({UserRoleFactory.user()}))
            >>> user.has_any_permission(Permission.READ_OWN, Permission.READ_ANY)
            True
        """
        if not permissions:
            return False
        return any(self.has_permission(p) for p in permissions)

    def has_all_permissions(self, *permissions: Permission) -> bool:
        """Check if the user has all of the specified permissions.

        Args:
            *permissions: One or more permissions to check

        Returns:
            bool: True if the user has all of the permissions

        Example:
            >>> user = User(..., roles=frozenset({UserRoleFactory.admin()}))
            >>> user.has_all_permissions(Permission.READ_ANY, Permission.UPDATE_ANY)
            True
        """
        if not permissions:
            return False
        return all(self.has_permission(p) for p in permissions)

    def get_role(self, role_name: str) -> Optional[UserRole]:
        """Get a role by name from the user's roles.

        Args:
            role_name: The name of the role to get

        Returns:
            Optional[UserRole]: The role if found, None otherwise

        Example:
            >>> user = User(..., roles=frozenset({UserRoleFactory.user()}))
            >>> role = user.get_role('user')
            >>> role.name
            'user'
        """
        return next((role for role in self.roles if role.name == role_name), None)

    def add_role(self, role: UserRole) -> "User":
        """Add a role to the user and return a new User instance.

        Args:
            role: The role to add

        Returns:
            User: A new User instance with the added role

        Example:
            >>> user = User(..., roles=frozenset({UserRoleFactory.user()}))
            >>> admin_role = UserRoleFactory.admin()
            >>> updated_user = user.add_role(admin_role)
            >>> admin_role in updated_user.roles
            True
        """
        if role in self.roles:
            return self
        return self.with_updates(
            roles=frozenset({*self.roles, role}), updated_at=datetime.now(timezone.utc)
        )

    def remove_role(self, role_name: str) -> "User":
        """Remove a role from the user and return a new User instance.

        Args:
            role_name: The name of the role to remove

        Returns:
            User: A new User instance with the role removed

        Example:
            >>> user = User(..., roles=frozenset({UserRoleFactory.user()}))
            >>> updated_user = user.remove_role('user')
            >>> len(updated_user.roles)
            0
        """
        if not any(role.name == role_name for role in self.roles):
            return self
        return self.with_updates(
            roles=frozenset(r for r in self.roles if r.name != role_name),
            updated_at=datetime.now(timezone.utc),
        )

    def update_roles(self, roles: FrozenSet[UserRole]) -> "User":
        """Update the user's roles and return a new User instance.

        This method creates a new User instance with the updated roles
        and updates the 'updated_at' timestamp. The original user instance
        remains unchanged to maintain immutability.

        Args:
            roles: The new set of roles for the user. This will completely
                  replace the existing roles.

        Returns:
            User: A new User instance with updated roles and updated timestamp

        Example:
            >>> user = User(...)
            >>> admin_role = UserRoleFactory.admin()
            >>> updated_user = user.update_roles(frozenset({admin_role}))
            >>> admin_role in updated_user.roles
            True

        Note:
            This operation is idempotent. If the roles haven't changed,
            it will return a new instance with the same roles but updated timestamp.
        """
        if self.roles == roles:
            return self.with_updates(updated_at=datetime.now(timezone.utc))

        return self.with_updates(roles=roles, updated_at=datetime.now(timezone.utc))

    def verify_email(self) -> "User":
        """Verify the user's email address and return a new User instance.

        This method marks the user's email as verified by creating a new User instance
        with an updated status. The original user instance remains unchanged to maintain
        immutability.

        The operation will fail if:
        - The user doesn't have an email address
        - The user's account is not enabled
        - The email is already verified

        Returns:
            User: A new User instance with is_verified=True in the status

        Raises:
            ValueError: If the user has no email, account is disabled,
             or email is already verified

        Example:
            >>> user = User(
            ...     email=Email("test@example.com"),
            ...     status=UserStatus(is_enabled=True, is_verified=False),
            ...     ...  # other required fields
            ... )
            >>> verified_user = user.verify_email()
            >>> verified_user.status.is_verified
            True

        Note:
            - This operation is idempotent
            - Returns a new User instance to maintain immutability
            - Updates the 'updated_at' timestamp automatically
        """
        if not hasattr(self, "email") or not self.email:
            raise ValueError("Cannot verify email: No email address set")

        if not self.status.is_enabled:
            raise ValueError("Cannot verify email: Account is disabled")

        if self.status.is_verified:
            return self

        new_status = self.status.is_email_verified()
        return self.with_updates(
            status=new_status, updated_at=datetime.now(timezone.utc)
        )

    def disable_account(self) -> "User":
        """Disable the user account and return a new User instance.

        This method creates a new User instance with the account disabled.
        A disabled account cannot be used for authentication until it is
        re-enabled. The original user instance remains unchanged.

        Returns:
            User: A new User instance with is_enabled=False in the status

        Example:
            >>> user = User(...)  # Active user
            >>> disabled_user = user.disable_account()
            >>> disabled_user.status.is_enabled
            False

        Note:
            This operation is idempotent. If the account is already disabled,
            it will return the same instance.
        """
        if not self.status.is_enabled:
            return self

        new_status = self.status.disable_account()
        return self.with_updates(
            status=new_status, updated_at=datetime.now(timezone.utc)
        )

    def soft_delete(self) -> "User":
        """Mark the user as deleted and return a new User instance.

        This performs a soft delete by setting the deleted_at timestamp.
        The user record remains in the database but is marked as deleted.
        The original user instance remains unchanged to maintain immutability.

        Returns:
            User: A new User instance with deleted_at set to current time

        Example:
            >>> user = User(...)  # Active user
            >>> deleted_user = user.soft_delete()
            >>> deleted_user.deleted_at is not None
            True
            >>> deleted_user.status.is_enabled
            False

        Note:
            This operation is idempotent. If the user is already soft-deleted,
            it will return the same instance. The account is automatically
            disabled when soft-deleted.
        """
        if self.deleted_at is not None:
            return self

        # Disable the account when soft-deleting
        new_status = self.status.disable_account()

        return self.with_updates(
            status=new_status,
            deleted_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    def enable_account(self) -> "User":
        """Enable the user account and return a new User instance.

        This method creates a new User instance with the account enabled.
        An enabled account can be used for authentication. The original
        user instance remains unchanged to maintain immutability.

        Returns:
            User: A new User instance with is_enabled=True in the status

        Example:
            >>> user = User(...)  # Disabled user
            >>> enabled_user = user.enable_account()
            >>> enabled_user.status.is_enabled
            True

        Note:
            This operation is idempotent. If the account is already enabled,
            it will return the same instance with an updated timestamp.
        """
        if self.status.is_enabled:
            return self.with_updates(updated_at=datetime.now(timezone.utc))

        new_status = self.status.enable_account()
        return self.with_updates(
            status=new_status, updated_at=datetime.now(timezone.utc)
        )

    def restore(self) -> "User":
        """Restore a soft-deleted user and return a new User instance.

        This restores a previously soft-deleted user by setting deleted_at to None.
        The account remains disabled after restoration and must be explicitly
        enabled. The original user instance remains unchanged.

        Returns:
            User: A new User instance with deleted_at set to None

        Example:
            >>> deleted_user = User(..., deleted_at=datetime.now(timezone.utc))
            >>> restored_user = deleted_user.restore()
            >>> restored_user.deleted_at is None
            True
            >>> restored_user.status.is_enabled
            False

        Note:
            This operation is idempotent. If the user is not deleted,
            it will return the same instance.
        """
        if self.deleted_at is None:
            return self

        return self.with_updates(deleted_at=None, updated_at=datetime.now(timezone.utc))

    def with_updates(self, **updates) -> "User":
        """Return a new User instance with the specified updates.

        This is the primary method for creating modified copies of a User instance.
        It uses dataclasses.replace() under the hood to create a new instance
        with the specified fields updated. All other fields remain unchanged.

        Args:
            **updates: Keyword arguments where keys are attribute names and
                     values are the new values for those attributes.

        Returns:
            User: A new User instance with the specified updates applied

        Example:
            >>> user = User(first_name="John", last_name="Doe",
            ... email=Email("john@example.com"))
            >>> updated = user.with_updates(first_name="Jonathan")
            >>> updated.first_name
            'Jonathan'
            >>> updated.last_name  # Unchanged from original
            'Doe'

        Note:
            - This method always creates a new instance, ensuring immutability
            - The 'updated_at' field is automatically set to the current time
            - For nested objects (like status), the entire object should be replaced
        """
        # Always update the updated_at timestamp
        if "updated_at" not in updates:
            updates["updated_at"] = datetime.now(timezone.utc)

        return dataclass_replace(self, **updates)

    def __eq__(self, other: object) -> bool:
        """Compare two User instances for equality.

        Two users are considered equal if they have the same ID.
        This is consistent with the concept of entity identity in DDD.

        Args:
            other: The object to compare with

        Returns:
            bool: True if the objects are the same user, False otherwise

        Example:
            >>> user1 = User(id="123", ...)
            >>> user2 = User(id="123", ...)
            >>> user1 == user2
            True
            >>> user1 == "not a user"
            False
        """
        if not isinstance(other, User):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Return a hash value for the user.

        The hash is based on the user's ID, ensuring consistency with __eq__.

        Returns:
            int: A hash value for the user

        Example:
            >>> user = User(id="123", ...)
            >>> hash_value = hash(user)

        Note:
            This allows User instances to be used in sets and as dictionary keys.
        """
        return hash(self.id)

    def __str__(self) -> str:
        """Return a concise string representation of the user.

        This provides a human-readable string that identifies the user
        without exposing sensitive information.

        Returns:
            str: A string in the format "User(id=..., email=..., name=...)"

        Example:
            >>> user = User(id="123", email=Email("user@example.com"),
            ...            first_name="John", last_name="Doe")
            >>> str(user)
            'User(id=123, email=user@example.com, name=John Doe)'
        """
        return f"User(id={self.id}, email={self.email}, name={self.full_name})"

    def __repr__(self) -> str:
        """Return a detailed string representation of the user for debugging.

        This provides a more detailed representation than __str__, including
        the user's roles and account status. It's primarily intended for
        debugging and logging purposes.

        Returns:
            str: A detailed string representation of the user

        Example:
            >>> user = User(
            ...     id="123",
            ...     email=Email("user@example.com"),
            ...     first_name="John",
            ...     last_name="Doe",
            ...     roles={UserRole.USER}
            ... )
            >>> repr(user)
            'User(id=123, email=user@example.com, name=John Doe,
             roles={...}, active=True, verified=False)'
        """
        return (
            f"User(id={self.id}, email={self.email}, "
            f"name={self.full_name}, roles={self.roles}, "
            f"active={self.status.is_enabled}, verified={self.status.is_verified})"
        )
