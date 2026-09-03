"""SQLAlchemy declarative base for ForgeFlow models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared metadata root. Domain models are added in Milestone 1."""
