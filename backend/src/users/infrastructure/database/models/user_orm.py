"""SQLAlchemy ORM models for users."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Set

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database.base import Base
from src.users.domain.entities.user import User
from src.users.domain.value_objects import Email, HashedPassword
from src.users.domain.value_objects.user_role_factory import RoleType, UserRoleFactory
from src.users.domain.value_objects.user_status import UserStatus

if TYPE_CHECKING:
    from .token_orm import TokenORM


class UserORM(Base):
    """SQLAlchemy ORM model for users.

    This model maps to the 'users' table in the database and includes all fields
    from the User domain entity except for token-related fields.
    """

    __tablename__ = "users"

    __table_args__ = (
        # Indexes for common query patterns
        Index("ix_user_email", "email", unique=True),
        Index("ix_user_username", "username", unique=True),
        Index("is_enabled_account", "is_verified_email"),
        # Check constraints
        CheckConstraint("email IS NOT NULL AND email != ''", name="email_required"),
        CheckConstraint(
            "username IS NOT NULL AND username != ''", name="username_required"
        ),
        CheckConstraint("hashed_password IS NOT NULL", name="password_required"),
    )

    # Core Identity
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="User's unique email address",
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="User's unique username",
    )
    first_name: Mapped[str] = mapped_column(
        String(100), nullable=False, doc="User's first name"
    )
    last_name: Mapped[str] = mapped_column(
        String(100), nullable=False, doc="User's last name"
    )

    # Profile
    bio: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="User's biography/description"
    )
    profile_picture: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, doc="URL to the user's profile picture"
    )

    # Authentication & Security
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, doc="Salted and hashed password"
    )
    is_enabled_account: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, doc="Whether the account is enabled"
    )
    is_verified_email: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the email has been verified",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="When the user account was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="When the user account was last updated",
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the user account was soft-deleted (if applicable)",
    )
    # Roles and Permissions
    roles: Mapped[Set[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=lambda: {"user"},  # Default role is 'user'
        server_default="{user}",
        doc="User's roles that determine permissions",
    )

    # Relationship to tokens (one-to-many)
    tokens: Mapped[List["TokenORM"]] = relationship(
        "TokenORM", back_populates="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    @classmethod
    def from_entity(cls, user: "User") -> "UserORM":
        """Create ORM model from domain model.

        Args:
            user: The domain model user instance

        Returns:
            UserORM: A new ORM instance with data from the domain model
        """
        return cls(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            bio=user.bio,
            profile_picture=user.profile_picture,
            is_enabled_account=user.status.is_enabled,
            is_verified_email=user.status.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            deleted_at=user.deleted_at,
            roles={role.name for role in user.roles},
        )

    def to_entity(self) -> "User":
        """Convert ORM model to domain model.

        Returns:
            User: A domain model instance with data from the ORM
        """

        # Create value objects
        email = Email(self.email) if not isinstance(self.email, Email) else self.email
        hashed_password = (
            HashedPassword(self.hashed_password)
            if not isinstance(self.hashed_password, HashedPassword)
            else self.hashed_password
        )

        # Create roles based on role names
        roles = set()
        for role_name in self.roles or set():
            try:
                role_type = RoleType(role_name.lower())
                if role_type == RoleType.ADMIN:
                    roles.add(UserRoleFactory().admin())
                elif role_type == RoleType.MODERATOR:
                    roles.add(UserRoleFactory().moderator())
                else:
                    roles.add(UserRoleFactory().user())
            except ValueError:
                # If role name is not in RoleType, default to user role
                roles.add(UserRoleFactory().user())

        # Create UserStatus value object
        status = UserStatus(
            is_enabled=self.is_enabled_account,
            is_verified=self.is_verified_email,
        )

        return User(
            id=self.id,
            email=email,
            hashed_password=hashed_password,
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name,
            bio=self.bio,
            profile_picture=self.profile_picture,
            status=status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
            roles=frozenset(roles),
        )
