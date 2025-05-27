"""Shared domain exceptions."""


class DomainError(Exception):
    """Base class for domain errors."""
    pass


class ValidationError(DomainError):
    """Raised when domain validation fails."""
    pass


class EntityNotFoundError(DomainError):
    """Raised when an entity is not found."""
    pass


class EntityAlreadyExistsError(DomainError):
    """Raised when an entity with the same identity already exists."""
    pass


class ConcurrencyError(DomainError):
    """Raised when a concurrency conflict occurs."""
    pass


class RepositoryError(DomainError):
    """Base class for repository errors."""
    pass


class UnitOfWorkError(DomainError):
    """Base class for unit of work errors."""
    pass
