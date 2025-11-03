"""Base repository class for database operations."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

ModelType = TypeVar("ModelType", bound=SQLModel)


class AbstractRepository(ABC, Generic[ModelType]):
    """Abstract base repository for database operations."""

    def __init__(self, session: AsyncSession, model: type[ModelType]):
        """
        Initialize the repository with a session and model.

        Parameters
        ----------
        session : AsyncSession
            Database session for operations.
        model : type[ModelType]
            SQLModel class for this repository.
        """
        self.session = session
        self.model = model

    async def create(self, **kwargs: Any) -> ModelType:
        """
        Create a new instance of the model.

        Parameters
        ----------
        **kwargs : Any
            Model attributes to set.

        Returns
        -------
        ModelType
            Created model instance.

        Raises
        ------
        Exception
            If creation fails.
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, id: int) -> ModelType | None:
        """
        Get a model instance by its ID.

        Parameters
        ----------
        id : int
            Primary key ID.

        Returns
        -------
        ModelType | None
            Model instance if found, None otherwise.
        """
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self, limit: int | None = None, offset: int = 0) -> list[ModelType]:
        """
        Get all instances of the model.

        Parameters
        ----------
        limit : int | None, optional
            Maximum number of results, by default None.
        offset : int, optional
            Number of results to skip, by default 0.

        Returns
        -------
        list[ModelType]
            List of model instances.
        """
        stmt = select(self.model).offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: int, **kwargs: Any) -> ModelType | None:
        """
        Update a model instance by ID.

        Parameters
        ----------
        id : int
            Primary key ID.
        **kwargs : Any
            Attributes to update.

        Returns
        -------
        ModelType | None
            Updated model instance if found, None otherwise.
        """
        instance = await self.get_by_id(id)
        if not instance:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: int) -> bool:
        """
        Delete a model instance by ID.

        Parameters
        ----------
        id : int
            Primary key ID.

        Returns
        -------
        bool
            True if deleted, False if not found.
        """
        instance = await self.get_by_id(id)
        if not instance:
            return False

        await self.session.delete(instance)
        await self.session.commit()
        return True

    async def count(self) -> int:
        """
        Count total number of instances.

        Returns
        -------
        int
            Total count of instances.
        """
        stmt = select(self.model)
        result = await self.session.execute(stmt)
        return len(result.scalars().all())

    @abstractmethod
    async def find_by(self, **criteria: Any) -> list[ModelType]:
        """
        Find instances by criteria.

        Parameters
        ----------
        **criteria : Any
            Search criteria.

        Returns
        -------
        list[ModelType]
            List of matching instances.
        """


class AbstractSqlRepository(AbstractRepository[ModelType]):
    """SQL-specific repository implementation."""

    async def find_by(self, **criteria: Any) -> list[ModelType]:
        """
        Find instances by criteria using SQL WHERE clauses.

        Parameters
        ----------
        **criteria : Any
            Search criteria as keyword arguments.

        Returns
        -------
        list[ModelType]
            List of matching instances.
        """
        stmt = select(self.model)
        for key, value in criteria.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
