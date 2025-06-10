"""Interface for user registration service."""

from abc import ABC, abstractmethod

from src.users.domain.interfaces.email_service import IEmailService
from src.users.domain.interfaces.password_service import IPasswordService
from src.users.domain.interfaces.unit_of_work import IUnitOfWork
from src.users.domain.schemas.user_schemas import (
    UserProfileResponse,
    UserRegisterRequest,
)


class IUserRegistrationService(ABC):
    """Interface for user registration service."""

    def __init__(
        self,
        uow: IUnitOfWork,
        password_service: IPasswordService,
        email_service: IEmailService,
    ) -> None:
        """Initialize the user registration service.

        Args:
            uow: Unit of Work instance for managing transactions and repositories
            password_service: Service for password hashing and verification
            email_service: Service for sending emails
        """
        self.uow = uow
        self.password_service = password_service
        self.email_service = email_service

    @abstractmethod
    async def register_user(
        self, user_data: UserRegisterRequest
    ) -> UserProfileResponse:
        """Register a new user.
        
        Args:
            user_data: The user registration data
            
        Returns:
            UserProfile: The created user's profile information
            
        Raises:
            EmailAlreadyExistsError: If the email is already registered
            UsernameAlreadyExistsError: If the username is already taken
            UserRegistrationError: If registration fails for any other reason
        """
        ...
