"""Token service for managing authentication tokens."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)
from uuid import UUID, uuid4

from jose import JWTError, jwt

from src.users.domain.entities.token import Token
from src.users.domain.entities.user import User
from src.users.domain.exceptions import (
    TokenError,
    TokenExpiredError,
    TokenRevokedError,
)
from src.users.domain.interfaces.token_service import ITokenService
from src.users.domain.interfaces.unit_of_work import IUnitOfWork
from src.users.domain.schemas.token_schemas import TokenVerificationResult
from src.users.domain.value_objects.token_value_objects import (
    TokenExpiry,
    TokenPayload,
    TokenScope,
    TokenStatus,
    TokenString,
    TokenType,
)

logger = logging.getLogger(__name__)

# Type variable for the Unit of Work
T = TypeVar("T", bound=IUnitOfWork)


class TokenService(ITokenService):
    """Service handling token management, validation, and generation.

    This service is responsible for all token-related operations including:
    - Generating JWT tokens
    - Validating tokens
    - Managing token lifecycle
    - Handling token refresh flow
    - CRUD operations for tokens
    """

    def __init__(
        self,
        uow: IUnitOfWork,
        secret_key: str,
        algorithm: str,
        access_token_expire_seconds: int,
        refresh_token_expire_seconds: int,
    ) -> None:
        """Initialize token service with required dependencies.

        Args:
            uow_factory: Factory function that returns a Unit of Work context manager
            secret_key: Secret key for JWT token signing
            algorithm: Algorithm for JWT token signing
            access_token_expire_seconds: Expiration time for access tokens in seconds
            refresh_token_expire_seconds: Expiration time for refresh tokens in seconds
        """
        self.uow = uow
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_seconds = access_token_expire_seconds
        self.refresh_token_expire_seconds = refresh_token_expire_seconds

        if not self.secret_key:
            logger.warning(
                "Using default or insecure SECRET_KEY. "
                "Please set a strong SECRET_KEY in your environment variables."
            )

        # Validate required configuration
        if not all([self.secret_key, self.algorithm]):
            raise ValueError(
                "TokenService requires secret_key and algorithm to be provided"
            )

        if not all(
            [self.access_token_expire_seconds, self.refresh_token_expire_seconds]
        ):
            raise ValueError(
                "Token expiration times must be provided for access and refresh tokens"
            )

    # ===== Core Token Operations =====

    async def create_token(
        self,
        user_id: str,
        token_type: TokenType,
        expires_in_seconds: int,
        scopes: Optional[Set[str]] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        token_string: Optional[str] = None,
    ) -> Token:
        """Create a new token for a user using value objects.

        Args:
            user_id: ID of the user this token belongs to
            token_type: Type of token to create
            expires_in_seconds: Token lifetime in seconds
            scopes: Set of scopes for the token
            user_agent: User agent that requested the token
            ip_address: IP address that requested the token
            meta: Additional metadata for the token

        Returns:
            Token: The created token entity

        Raises:
            ValueError: If user_id is invalid
            TokenError: If token creation fails
        """
        if not user_id:
            raise ValueError("User ID is required")

        try:
            # Create token expiry
            token_expiry = TokenExpiry.from_now(expires_in_seconds)
            token_scopes = TokenScope(scopes or set())

            # Generate an opaque token if none provided
            if token_string is None:
                token_string = secrets.token_urlsafe(
                    32
                )  # Generate a secure random token

            token_string = TokenString(token_string)

            # Create token entity with placeholder token
            token = Token.create(
                token=token_string,
                user_id=user_id,
                token_type=token_type,
                expiry=token_expiry,
                scopes=token_scopes,
                user_agent=user_agent,
                ip_address=ip_address,
                meta=meta or {},
            )

            # Save the token to get an ID
            async with self.uow.transaction():
                created_token = await self.uow.tokens.create_token(token)
                await self.uow.commit()

            logger.info("Created new %s token for user %s", token_type, user_id)
            return created_token

        except Exception as e:
            logger.error("Error creating token: %s", str(e), exc_info=True)
            raise TokenError("Failed to create token") from e

    def _create_jwt_payload(
        self,
        user: User,
        token_type: TokenType,
        expires_in_seconds: int,
        scopes: Optional[Set[str]] = None,
        **extra_claims,
    ) -> Dict[str, Any]:
        """Create a JWT payload with standard claims.

        Args:
            user: The user to create the token for
            token_type: Type of token (access, refresh, etc.)
            expires_in_seconds: Token lifetime in seconds
            scopes: Set of scopes for the token
            **extra_claims: Additional claims to include in the token

        Returns:
            Dictionary containing the JWT claims
        """
        expiry = TokenExpiry.from_now(seconds=expires_in_seconds)
        scopes = scopes or {"*"}

        payload = {
            "sub": str(user.id),
            "type": token_type,
            "jti": str(uuid4()),
            "iat": datetime.now(timezone.utc),
            "exp": expiry.expires_at,
            "scopes": list(scopes),
            "email": user.email,
            "username": user.username,
            "roles": [role.name for role in user.roles],
            "is_verified": user.status.is_verified,
            **extra_claims,
        }

        return payload

    async def create_access_token(
        self,
        user: User,
        scopes: Optional[Set[str]] = None,
        request_info: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, Token]:
        """Create a JWT access token for the user.

        Args:
            user: The user to create the token for
            scopes: Set of scopes for the token (defaults to all scopes)
            request_info: Optional dictionary containing request information
                         (e.g., user_agent, ip_address)

        Returns:
            Tuple[str, Token]: JWT token string and the created Token entity

        Raises:
            ValueError: If user is invalid
            TokenError: If token creation fails
        """
        if not user or not user.id:
            raise ValueError("Invalid user")

        try:
            # Create JWT payload and encode it
            payload = self._create_jwt_payload(
                user=user,
                token_type=TokenType.ACCESS,
                expires_in_seconds=self.access_token_expire_seconds,
                scopes=scopes,
            )

            # Encode the JWT token
            jwt_token = self._encode_jwt(payload)

            # Create the token entity with the JWT token string
            token = await self.create_token(
                user_id=user.id,
                token_type=TokenType.ACCESS,
                expires_in_seconds=self.access_token_expire_seconds,
                scopes=scopes,
                user_agent=request_info.get("user_agent") if request_info else None,
                ip_address=request_info.get("ip_address") if request_info else None,
                meta={
                    "jti": payload["jti"],
                    "email": user.email,
                    "username": user.username,
                    "roles": [role.name for role in user.roles],
                    "is_verified": user.status.is_verified,
                },
                token_string=jwt_token,
            )

            return jwt_token, token

        except Exception as e:
            logger.error(
                "Failed to create access token",
                extra={
                    "user_id": str(user.id) if user and hasattr(user, "id") else None,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise TokenError("Failed to create access token") from e

    def _encode_jwt(self, payload: Dict[str, Any]) -> str:
        """Encode a JWT token string.

        Args:
            payload: JWT payload

        Returns:
            JWT token string
        """
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def _decode_jwt(self, token: str) -> Dict[str, Any]:
        """Decode a JWT token string.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            TokenExpiredError: If token has expired
            TokenError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={
                    "verify_signature": True,
                    "verify_aud": False,
                    "verify_iss": False,
                },
            )

            # Convert timestamp back to datetime
            payload["iat"] = datetime.fromtimestamp(payload["iat"], timezone.utc)
            payload["exp"] = datetime.fromtimestamp(payload["exp"], timezone.utc)

            return TokenPayload(**payload)

        except JWTError as e:
            logger.error("Error decoding JWT: %s", str(e), exc_info=True)
            if "exp" in str(e):
                raise TokenExpiredError("Token has expired") from e
            raise TokenError("Invalid token") from e

    # ===== Token Management =====

    async def get_token_by_value(self, token_str: str) -> Optional[Token]:
        """Get a token by its string value.

        Args:
            token_str: The token string to look up

        Returns:
            Optional[Token]: The token if found, None otherwise
        """
        try:
            async with self.uow.transaction():
                return await self.uow.tokens.get_by_token(token_str)
        except Exception as e:
            logger.error("Error retrieving token: %s", str(e), exc_info=True)
            return None

    async def get_user_tokens(
        self,
        user_id: str,
        active_only: bool = True,
    ) -> List[Token]:
        """Get all tokens for a user.

        Args:
            user_id: ID of the user
            active_only: Whether to return only active tokens

        Returns:
            List[Token]: List of tokens matching the criteria
        """
        try:
            async with self.uow.transaction():
                tokens = await self.uow.tokens.get_active_tokens_for_user(user_id)
                if active_only:
                    tokens = [t for t in tokens if t.status == TokenStatus.ACTIVE]
                return tokens
        except Exception as e:
            logger.error("Error retrieving user tokens: %s", str(e), exc_info=True)
            return []

    async def delete_expired_tokens(self) -> int:
        """Delete all expired tokens from the database.

        Returns:
            int: Number of tokens deleted
        """
        try:
            async with self.uow.transaction():
                now = datetime.now(timezone.utc)
                count = await self.uow.tokens.delete_expired_tokens(now)

                if count > 0:
                    logger.info("Deleted %d expired tokens", count)

                return count

        except Exception as e:
            logger.error("Error deleting expired tokens: %s", str(e), exc_info=True)
            return 0

    # ===== Token Verification =====

    async def verify_token(
        self,
        token_str: str,
        token_type: Optional[TokenType] = None,
        required_scopes: Optional[Set[str]] = None,
    ) -> TokenVerificationResult:
        """Verify a token and return verification result.

        Args:
            token_str: The token to verify
            token_type: Expected token type
            required_scopes: Required scopes

        Returns:
            TokenVerificationResult: Verification result with user, token, and payload

        Raises:
            TokenExpiredError: If the token has expired
            TokenRevokedError: If the token has been revoked
            InvalidTokenError: If the token is invalid
        """
        try:
            # Decode the JWT
            try:
                payload = self._decode_jwt(token_str)
            except TokenExpiredError:
                return TokenVerificationResult(
                    is_valid=False, error="Token has expired"
                )
            except TokenError:
                return TokenVerificationResult(is_valid=False, error="Invalid token")

            # Verify token type if specified
            if token_type and payload.type != token_type:
                return TokenVerificationResult(
                    is_valid=False, error=f"Invalid token type: expected {token_type}"
                )

            # Get the token from database
            token = await self.get_token_by_value(token_str)
            if not token:
                return TokenVerificationResult(is_valid=False, error="Token not found")

            # Check token status
            if token.status != TokenStatus.ACTIVE:
                if token.status == TokenStatus.EXPIRED:
                    raise TokenExpiredError("Token has expired")
                elif token.status == TokenStatus.REVOKED:
                    raise TokenRevokedError("Token has been revoked")
                return TokenVerificationResult(
                    is_valid=False, error=f"Token is {token.status.value}"
                )

            # Check scopes if required
            if required_scopes:
                token_scopes = TokenScope(set(payload.scopes or []))
                if not token_scopes.has_all_scopes(*required_scopes):
                    return TokenVerificationResult(
                        is_valid=False, error="Insufficient permissions"
                    )

            # Get the user
            try:
                user_id = UUID(payload.sub)
                async with self.uow.transaction():
                    user = await self.uow.users.get_user_by_id(user_id)
                    if not user:
                        return TokenVerificationResult(
                            is_valid=False, error="User not found"
                        )

                    # Update last used timestamp
                    token.last_used_at = datetime.now(timezone.utc)
                    await self.uow.tokens.update_token(token)
                    await self.uow.commit()

                    return TokenVerificationResult(
                        is_valid=True, user=user, token=token, payload=payload
                    )

            except Exception as e:
                logger.error("Error fetching user: %s", str(e), exc_info=True)
                return TokenVerificationResult(
                    is_valid=False, error="Error verifying user"
                )

        except Exception as e:
            logger.error("Error verifying token: %s", str(e), exc_info=True)
            return TokenVerificationResult(
                is_valid=False, error="Internal server error"
            )

    async def create_refresh_token(
        self,
        user: User,
        parent_token_id: Optional[UUID] = None,
        request_info: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, Token]:
        """Create a refresh token for the user.

        Args:
            user: The user to create the token for
            parent_token_id: Optional ID of the parent access token
            request_info: Optional dictionary containing request information
                         (e.g., user_agent, ip_address)

        Returns:
            Tuple[str, Token]: Refresh token string (UUID) and the created Token entity

        Raises:
            ValueError: If user is invalid
        """
        if not user or not user.id:
            raise ValueError("Invalid user")

        # Create the refresh token entity with minimal user info
        token = await self.create_token(
            user_id=user.id,
            token_type=TokenType.REFRESH,
            expires_in_seconds=self.refresh_token_expire_seconds,
            scopes={"refresh_token"},
            user_agent=request_info.get("user_agent") if request_info else None,
            ip_address=request_info.get("ip_address") if request_info else None,
            meta={
                "parent_token_id": str(parent_token_id) if parent_token_id else None,
                # Only store minimal required user info in meta
                "user_id": str(user.id),
            },
        )

        # Update the token with the generated token string
        token = token.with_updates(
            token=TokenString(token.generate_opaque_token_string())
        )

        # Save the updated token with the token string
        async with self.uow.transaction():
            await self.uow.tokens.update_token(token)
            await self.uow.commit()

        # Return the raw UUID string as the refresh token
        return str(token.token), token

    async def revoke_token(
        self, token_identifier: Union[str, UUID], reason: str = "User logged out"
    ) -> bool:
        """Revoke a token by its string value or ID.

        Args:
            token_identifier: The token string or UUID to revoke
            reason: Reason for revocation

        Returns:
            bool: True if token was successfully revoked, False otherwise
        """
        try:
            async with self.uow.transaction():
                token = await self.uow.tokens.get_by_token(token_identifier)

                if not token:
                    logger.warning("Token not found: %s", token_identifier)
                    return False

                if token.status != TokenStatus.ACTIVE:
                    logger.info(
                        "Token %s is not active (status: %s)",
                        token_identifier,
                        token.status,
                    )
                    return False

                token.status = TokenStatus.REVOKED
                token.revoked_at = datetime.now(timezone.utc)
                token.revocation_reason = reason

                await self.uow.tokens.update_token(token)
                await self.uow.commit()
                logger.info(
                    "Token %s revoked successfully. Reason: %s",
                    token_identifier,
                    reason,
                )
                return True

        except Exception as e:
            logger.error(
                "Error revoking token %s: %s", token_identifier, str(e), exc_info=True
            )
            return False

    async def revoke_user_tokens(
        self, user_id: UUID, reason: str = "User initiated logout"
    ) -> int:
        """Revoke all active tokens for a user.

        Args:
            user_id: ID of the user
            reason: Reason for revocation

        Returns:
            int: Number of tokens revoked
        """
        async with self.uow.transaction():
            tokens = await self.uow.tokens.get_active_tokens_for_user(user_id)
            revoked_count = 0

            for token in tokens:
                token.status = TokenStatus.REVOKED
                token.revoked_at = datetime.now(timezone.utc)
                token.revocation_reason = reason
                await self.uow.tokens.update_token(token)
                revoked_count += 1

            await self.uow.commit()
            return revoked_count

    async def create_email_verification_token(
        self,
        user: User,
        request_info: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, Token]:
        """Create an email verification token for a user.

        Args:
            user: The user to create the token for
            request_info: Optional dictionary containing request information
                        (e.g., user_agent, ip_address)

        Returns:
            Tuple[str, Token]: (token_string, token_entity)

        Raises:
            ValueError: If user is invalid
        """
        if not user or not user.id:
            raise ValueError("Invalid user")

        # Create a token that expires in 24 hours by default
        # Independent from global settings
        expires_in_seconds = 60 * 60 * 24  # 24 hours in seconds

        # Create the token with email verification scope
        token = await self.create_token(
            user_id=str(user.id),
            token_type=TokenType.EMAIL_VERIFICATION,
            expires_in_seconds=expires_in_seconds,
            scopes={"verify_email"},
            user_agent=request_info.get("user_agent") if request_info else None,
            ip_address=request_info.get("ip_address") if request_info else None,
        )

        # Encode the token as JWT
        payload = TokenPayload(
            sub=str(user.id),
            type=TokenType.EMAIL_VERIFICATION,
            jti=str(token.id),
            iat=datetime.now(timezone.utc),
            exp=datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds),
            scopes=["verify_email"],
            meta={"purpose": "email_verification"},
        )

        token_string = self._encode_jwt(payload)
        return token_string, token

    async def refresh_access_token(
        self, refresh_token: str
    ) -> Optional[Tuple[str, str]]:
        """Generate a new access token using a valid refresh token.

        Implements refresh token rotation for enhanced security.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Optional[Tuple[str, str]]:
                (new_access_token, new_refresh_token) if successful,
                None otherwise
        """
        try:
            # Verify the refresh token using the main verification method
            result = await self.verify_token(refresh_token, TokenType.REFRESH)
            if not result.is_valid or not result.user or not result.token:
                return None

            user = result.user
            token = result.token

            # Create request info for new tokens
            request_info = {
                "user_agent": token.user_agent,
                "ip_address": token.ip_address,
            }

            # Create new access token
            access_token, _ = await self.create_access_token(
                user=user, request_info=request_info
            )

            # Revoke the old refresh token
            await self.revoke_token(
                token_identifier=token.id, reason="Refreshed with new token"
            )

            # Create a new refresh token
            _, new_refresh_token = await self.create_refresh_token(
                user=user, parent_token_id=token.id, request_info=request_info
            )

            return access_token, new_refresh_token

        except Exception as e:
            logger.error("Error refreshing access token: %s", str(e), exc_info=True)
            return None
