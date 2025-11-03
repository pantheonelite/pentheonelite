"""High-level helpers for loading API keys."""

from app.backend.db.repositories.api_key_repository import ApiKeyRepository
from sqlmodel.ext.asyncio.session import AsyncSession


class ApiKeyService:
    """Simple service to load API keys for requests."""

    def __init__(self, db: AsyncSession):
        self.repository = ApiKeyRepository(db)

    async def get_api_keys_dict(self) -> dict[str, str]:
        """Return all active API keys as a provider-to-key mapping."""
        api_keys = await self.repository.get_all_api_keys(include_inactive=False)
        return {key.provider: key.key_value for key in api_keys}

    async def get_api_key(self, provider: str) -> str | None:
        """Fetch a single API key value by provider identifier."""
        api_key = await self.repository.get_api_key_by_provider(provider)
        return api_key.key_value if api_key else None
