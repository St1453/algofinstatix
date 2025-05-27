"""Base SQLAlchemy model for all database models."""

from typing import Any

from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import MetaData

# Recommended naming convention for constraints and indexes
# See: https://alembic.sqlalchemy.org/en/latest/naming.html
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


@as_declarative(metadata=metadata)
class Base:
    """Base class for all SQLAlchemy models.

    Provides common functionality and configuration for all models.
    """

    id: Mapped[Any] = mapped_column(primary_key=True)

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate __tablename__ automatically from class name.

        Converts CamelCase class name to snake_case table name.
        """
        return (
            "".join(
                ["_" + i.lower() if i.isupper() else i for i in cls.__name__]
            ).lstrip("_") + "s"
        )

    def __repr__(self) -> str:
        """Return a string representation of the model."""
        return f"<{self.__class__.__name__} {self.id}>"
