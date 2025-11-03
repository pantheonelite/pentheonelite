"""Repository for ApiKey operations."""

from typing import Any

from app.backend.db.models import ApiKey
from app.backend.db.repositories.base_repository import AbstractSqlRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ApiKeyRepository(AbstractSqlRepository[ApiKey]):
    """Repository for ApiKey CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ApiKey)

    async def create_key(
        self,
        provider: str,
        key_value: str,
        description: str | None = None,
        is_active: bool = True,
    ) -> ApiKey:
        """
        Create a new API key.

        Parameters
        ----------
        provider : str
            API provider name.
        key_value : str
            API key value.
        description : str | None, optional
            Key description, by default None.
        is_active : bool, optional
            Whether the key is active, by default True.

        Returns
        -------
        ApiKey
            Created API key instance.
        """
        return await self.create(
            provider=provider,
            key_value=key_value,
            description=description,
            is_active=is_active,
        )

    async def get_by_provider(self, provider: str) -> ApiKey | None:
        """
        Get API key by provider.

        Parameters
        ----------
        provider : str
            Provider name to search for.

        Returns
        -------
        ApiKey | None
            API key if found, None otherwise.
        """
        stmt = select(ApiKey).where(ApiKey.provider == provider)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_active_keys(self) -> list[ApiKey]:
        """
        Get all active API keys.

        Returns
        -------
        list[ApiKey]
            List of active API keys.
        """
        return await self.find_by(is_active=True)

    async def update_key_status(
        self,
        key_id: int,
        is_active: bool,
        description: str | None = None,
    ) -> ApiKey | None:
        """
        Update API key status.

        Parameters
        ----------
        key_id : int
            Key ID to update.
        is_active : bool
            New active status.
        description : str | None, optional
            New description, by default None.

        Returns
        -------
        ApiKey | None
            Updated key if found, None otherwise.
        """
        update_data: dict[str, Any] = {"is_active": is_active}

        if description is not None:
            update_data["description"] = description

        return await self.update(key_id, **update_data)

    async def update_last_used(self, key_id: int) -> ApiKey | None:
        """
        Update the last used timestamp for a key.

        Parameters
        ----------
        key_id : int
            Key ID to update.

        Returns
        -------
        ApiKey | None
            Updated key if found, None otherwise.
        """
        from datetime import datetime

        return await self.update(key_id, last_used=datetime.utcnow())

    async def get_keys_by_provider_pattern(self, pattern: str) -> list[ApiKey]:
        """
        Get keys by provider name pattern.

        Parameters
        ----------
        pattern : str
            Provider name pattern to search for.

        Returns
        -------
        list[ApiKey]
            List of matching keys.
        """
        stmt = select(ApiKey).where(ApiKey.provider.ilike(f"%{pattern}%")).order_by(ApiKey.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_or_update_api_key(
        self,
        provider: str,
        key_value: str,
        description: str | None = None,
        is_active: bool = True,
    ) -> ApiKey | None:
        """
        Create a new API key or update existing one for the provider.

        Parameters
        ----------
        provider : str
            API provider name.
        key_value : str
            API key value.
        description : str | None, optional
            Key description.
        is_active : bool, optional
            Whether the key is active.

        Returns
        -------
        ApiKey
            Created or updated API key instance.
        """
        existing = await self.get_by_provider(provider)
        if existing:
            return await self.update(
                existing.id,
                key_value=key_value,
                description=description,
                is_active=is_active,
            )
        return await self.create_key(provider, key_value, description, is_active)

    async def get_all_api_keys(self, include_inactive: bool = False) -> list[ApiKey]:
        """
        Get all API keys.

        Parameters
        ----------
        include_inactive : bool, optional
            Whether to include inactive keys.

        Returns
        -------
        list[ApiKey]
            List of API keys.
        """
        if include_inactive:
            return await self.get_all()
        return await self.get_active_keys()

    async def get_api_key_by_provider(self, provider: str) -> ApiKey | None:
        """
        Get API key by provider (alias for get_by_provider).

        Parameters
        ----------
        provider : str
            Provider name.

        Returns
        -------
        ApiKey | None
            API key if found.
        """
        return await self.get_by_provider(provider)

    async def update_api_key(
        self,
        provider: str,
        key_value: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> ApiKey | None:
        """
        Update an existing API key by provider.

        Parameters
        ----------
        provider : str
            Provider name.
        key_value : str | None, optional
            New key value.
        description : str | None, optional
            New description.
        is_active : bool | None, optional
            New active status.

        Returns
        -------
        ApiKey | None
            Updated key if found.
        """
        existing = await self.get_by_provider(provider)
        if not existing:
            return None

        update_data: dict[str, Any] = {}
        if key_value is not None:
            update_data["key_value"] = key_value
        if description is not None:
            update_data["description"] = description
        if is_active is not None:
            update_data["is_active"] = is_active

        return await self.update(existing.id, **update_data)

    async def delete_api_key(self, provider: str) -> bool:
        """
        Delete an API key by provider.

        Parameters
        ----------
        provider : str
            Provider name.

        Returns
        -------
        bool
            True if deleted, False if not found.
        """
        existing = await self.get_by_provider(provider)
        if not existing:
            return False
        return await self.delete(existing.id)

    async def deactivate_api_key(self, provider: str) -> bool:
        """
        Deactivate an API key without deleting it.

        Parameters
        ----------
        provider : str
            Provider name.

        Returns
        -------
        bool
            True if deactivated, False if not found.
        """
        result = await self.update_api_key(provider, is_active=False)
        return result is not None

    async def bulk_create_or_update(self, api_keys_data: list[dict[str, Any]]) -> list[ApiKey | None]:
        """
        Bulk create or update API keys.

        Parameters
        ----------
        api_keys_data : list[dict[str, Any]]
            List of API key data dictionaries.

        Returns
        -------
        list[ApiKey]
            List of created/updated API keys.
        """
        results = []
        for key_data in api_keys_data:
            result = await self.create_or_update_api_key(
                provider=key_data["provider"],
                key_value=key_data["key_value"],
                description=key_data.get("description"),
                is_active=key_data.get("is_active", True),
            )
            results.append(result)
        return results
