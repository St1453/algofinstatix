"""SQLAlchemy ORM models for users."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Set

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database.base import Base
from src.users.domain.entities.user import User as UserEntity
from src.users.domain.value_objects.user_role_factory import UserRoleFactory
from src.users.domain.value_objects.user_status import UserStatus

if TYPE_CHECKING:
    from src.users.domain.entities.user import User

    from .password_history_orm import PasswordHistoryORM
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
        Index("ix_user_status", "is_enabled_account", "is_verified_email"),
        # Check constraints
        CheckConstraint("email IS NOT NULL AND email != ''", name="email_required"),
        CheckConstraint(
            "username IS NOT NULL AND username != ''", name="username_required"
        ),
        CheckConstraint("hashed_password IS NOT NULL", name="password_required"),
        CheckConstraint(
            "first_name IS NULL OR length(first_name) > 0", name="valid_first_name"
        ),
        CheckConstraint(
            "last_name IS NULL OR length(last_name) > 0", name="valid_last_name"
        ),
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

    # Profile
    bio: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="User's biography/description"
    )
    profile_picture: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, doc="URL to the user's profile picture"
    )

    # Status Tracking
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,  # noqa: F821
        default=0,
        nullable=False,
        doc="Number of consecutive failed login attempts",
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the account will be automatically unlocked",
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
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, doc="When the user last logged in"
    )

    # MFA Settings
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether multi-factor authentication is enabled",
    )
    mfa_secret: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, doc="Encrypted MFA secret key"
    )

    # Roles and Permissions
    roles: Mapped[Set[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=lambda: {UserRoleFactory.user().name},
        server_default=f"{{{UserRoleFactory.user().name}}}",
        doc="User's roles that determine permissions",
    )

    # Relationships
    password_history: Mapped[List["PasswordHistoryORM"]] = relationship(
        "PasswordHistoryORM",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(PasswordHistoryORM.changed_at)",
        doc="History of user's previous passwords",
    )
    tokens: Mapped[List["TokenORM"]] = relationship(
        "TokenORM",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
        passive_deletes=True,
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
            failed_login_attempts=user.status.failed_login_attempts,
            locked_until=user.status.locked_until,
            password_changed_at=user.status.password_changed_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            deleted_at=user.deleted_at,
            last_login_at=user.status.last_login_at,
            last_failed_login=user.status.last_failed_login,
            mfa_enabled=user.mfa_enabled,
            mfa_secret=user.mfa_secret,
            password_reset_token=user.password_reset_token,
            password_reset_token_expires=user.password_reset_token_expires,
            roles={role.name for role in user.roles},
        )

    def to_entity(self) -> "User":
        """Convert ORM model to domain model.

        Returns:
            User: A domain model instance with data from the ORM
        """
        status = UserStatus(
            is_enabled=self.is_enabled_account,
            is_verified=self.is_verified_email,
            last_login_at=self.last_login_at,
            failed_login_attempts=self.failed_login_attempts,
            locked_until=self.locked_until,
            password_changed_at=self.password_changed_at,
            last_failed_login=self.last_failed_login,
        )

        return UserEntity(
            id=self.id,
            email=self.email,
            hashed_password=self.hashed_password,
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name,
            bio=self.bio,
            profile_picture=self.profile_picture,
            status=status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
            mfa_enabled=self.mfa_enabled,
            mfa_secret=self.mfa_secret,
            password_reset_token=self.password_reset_token,
            password_reset_token_expires=self.password_reset_token_expires,
            roles=frozenset(
                UserRoleFactory.get_role(role_name)
                for role_name in (self.roles or set())
            ),
        )
