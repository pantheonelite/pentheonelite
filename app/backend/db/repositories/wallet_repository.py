"""Repository for Wallet operations."""

from datetime import datetime
from typing import Any

from app.backend.db.models import Wallet
from app.backend.db.models.council import Council
from app.backend.db.repositories.base_repository import AbstractSqlRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class WalletRepository(AbstractSqlRepository[Wallet]):
    """Repository for Wallet CRUD operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository.

        Parameters
        ----------
        session : AsyncSession
            Database session
        """
        super().__init__(session, Wallet)

    async def create_wallet(
        self,
        council_id: int | None,
        exchange: str,
        api_key: str,
        secret_key: str,
        name: str | None = None,
        ca: str | None = None,
        is_active: bool = True,
    ) -> Wallet:
        """
        Create a new wallet for a council.

        Parameters
        ----------
        council_id : int | None
            Council ID this wallet belongs to (optional, can be set later)
        exchange : str
            Exchange name (e.g., "binance", "aster")
        api_key : str
            API key for trading
        secret_key : str
            Secret key for trading
        name : str | None
            Wallet name for display purposes (optional)
        ca : str | None
            Contract address (optional)
        is_active : bool
            Whether the wallet is active

        Returns
        -------
        Wallet
            Created wallet instance
        """
        wallet = Wallet(
            council_id=council_id,
            exchange=exchange,
            api_key=api_key,
            secret_key=secret_key,
            name=name,
            ca=ca,
            is_active=is_active,
            created_at=datetime.utcnow(),
        )

        self.session.add(wallet)
        await self.session.commit()
        await self.session.refresh(wallet)

        # Update council.wallet_id to point to this wallet if council_id is provided
        if council_id:
            council = await self.session.get(Council, council_id)
            if council:
                council.wallet_id = wallet.id
                await self.session.commit()
                await self.session.refresh(council)

        return wallet
    
    async def create_wallet_without_council(
        self,
        exchange: str,
        api_key: str,
        secret_key: str,
        name: str | None = None,
        ca: str | None = None,
        is_active: bool = True,
    ) -> Wallet:
        """
        Create a new wallet without a council (council_id can be set later).

        Parameters
        ----------
        exchange : str
            Exchange name (e.g., "binance", "aster")
        api_key : str
            API key for trading
        secret_key : str
            Secret key for trading
        name : str | None
            Wallet name for display purposes (optional)
        ca : str | None
            Contract address (optional)
        is_active : bool
            Whether the wallet is active

        Returns
        -------
        Wallet
            Created wallet instance
        """
        return await self.create_wallet(
            council_id=None,
            exchange=exchange,
            api_key=api_key,
            secret_key=secret_key,
            name=name,
            ca=ca,
            is_active=is_active,
        )
    
    async def update_wallet_council_id(
        self,
        wallet_id: int,
        council_id: int,
    ) -> Wallet | None:
        """
        Update wallet's council_id and link it to the council.

        Parameters
        ----------
        wallet_id : int
            Wallet ID to update
        council_id : int
            Council ID to link to

        Returns
        -------
        Wallet | None
            Updated wallet if found, None otherwise
        """
        wallet = await self.get_by_id(wallet_id)
        if not wallet:
            return None
        
        wallet.council_id = council_id
        wallet.updated_at = datetime.utcnow()
        
        # Update council.wallet_id to point to this wallet
        council = await self.session.get(Council, council_id)
        if council:
            council.wallet_id = wallet_id
        
        await self.session.commit()
        await self.session.refresh(wallet)
        
        return wallet

    async def get_wallet_by_council_id(self, council_id: int) -> Wallet | None:
        """
        Get wallet by council ID.

        Parameters
        ----------
        council_id : int
            Council ID to search for

        Returns
        -------
        Wallet | None
            Wallet if found, None otherwise
        """
        stmt = select(Wallet).where(Wallet.council_id == council_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_wallet_ca_by_id(self, wallet_id: int) -> str | None:
        """
        Get wallet CA (Contract Address) by wallet ID.

        Parameters
        ----------
        wallet_id : int
            Wallet ID

        Returns
        -------
        str | None
            Contract address if found, None otherwise
        """
        wallet = await self.get_by_id(wallet_id)
        return wallet.ca if wallet else None

    async def get_wallet_name_by_id(self, wallet_id: int) -> str | None:
        """
        Get wallet name by wallet ID.

        Parameters
        ----------
        wallet_id : int
            Wallet ID

        Returns
        -------
        str | None
            Wallet name if found, None otherwise
        """
        wallet = await self.get_by_id(wallet_id)
        return wallet.name if wallet else None

    async def update_wallet(
        self,
        council_id: int,
        exchange: str | None = None,
        api_key: str | None = None,
        secret_key: str | None = None,
        name: str | None = None,
        ca: str | None = None,
        is_active: bool | None = None,
    ) -> Wallet | None:
        """
        Update wallet for a council.

        Parameters
        ----------
        council_id : int
            Council ID
        exchange : str | None
            New exchange name (optional)
        api_key : str | None
            New API key (optional)
        secret_key : str | None
            New secret key (optional)
        name : str | None
            New wallet name (optional)
        ca : str | None
            New contract address (optional)
        is_active : bool | None
            New active status (optional)

        Returns
        -------
        Wallet | None
            Updated wallet if found, None otherwise
        """
        wallet = await self.get_wallet_by_council_id(council_id)
        if not wallet:
            return None

        update_data: dict[str, Any] = {}
        if exchange is not None:
            update_data["exchange"] = exchange
        if api_key is not None:
            update_data["api_key"] = api_key
        if secret_key is not None:
            update_data["secret_key"] = secret_key
        if name is not None:
            update_data["name"] = name
        if ca is not None:
            update_data["ca"] = ca
        if is_active is not None:
            update_data["is_active"] = is_active

        update_data["updated_at"] = datetime.utcnow()

        return await self.update(wallet.id, **update_data)

    async def delete_wallet(self, council_id: int) -> bool:
        """
        Delete wallet for a council.

        Parameters
        ----------
        council_id : int
            Council ID

        Returns
        -------
        bool
            True if deleted, False if not found
        """
        wallet = await self.get_wallet_by_council_id(council_id)
        if not wallet:
            return False

        # Clear council.wallet_id before deleting wallet
        council = await self.session.get(Council, council_id)
        if council and council.wallet_id == wallet.id:
            council.wallet_id = None
            await self.session.commit()

        return await self.delete(wallet.id)

    async def delete_wallet_by_id(self, wallet_id: int) -> bool:
        """
        Delete wallet by ID.

        Parameters
        ----------
        wallet_id : int
            Wallet ID

        Returns
        -------
        bool
            True if deleted, False if not found
        """
        # Get wallet to find council_id
        wallet = await self.get_by_id(wallet_id)
        if not wallet:
            return False

        # Clear council.wallet_id before deleting wallet
        council = await self.session.get(Council, wallet.council_id)
        if council and council.wallet_id == wallet_id:
            council.wallet_id = None
            await self.session.commit()

        return await self.delete(wallet_id)

    async def get_active_wallets(self) -> list[Wallet]:
        """
        Get all active wallets.

        Returns
        -------
        list[Wallet]
            List of active wallets
        """
        return await self.find_by(is_active=True)

    async def get_all_wallets(self) -> list[Wallet]:
        """
        Get all wallets.

        Returns
        -------
        list[Wallet]
            List of all wallets
        """
        return await self.get_all()

    async def create_or_update_wallet(
        self,
        council_id: int,
        exchange: str,
        api_key: str,
        secret_key: str,
        name: str | None = None,
        ca: str | None = None,
        is_active: bool = True,
    ) -> Wallet:
        """
        Create a new wallet or update existing one for a council.

        Parameters
        ----------
        council_id : int
            Council ID
        exchange : str
            Exchange name (e.g., "binance", "aster")
        api_key : str
            API key for trading
        secret_key : str
            Secret key for trading
        name : str | None
            Wallet name for display purposes (optional)
        ca : str | None
            Contract address (optional)
        is_active : bool
            Whether the wallet is active

        Returns
        -------
        Wallet
            Created or updated wallet instance
        """
        existing = await self.get_wallet_by_council_id(council_id)
        if existing:
            return await self.update_wallet(
                council_id=council_id,
                exchange=exchange,
                api_key=api_key,
                secret_key=secret_key,
                name=name,
                ca=ca,
                is_active=is_active,
            ) or existing
        return await self.create_wallet(
            council_id=council_id,
            exchange=exchange,
            api_key=api_key,
            secret_key=secret_key,
            name=name,
            ca=ca,
            is_active=is_active,
        )

    async def deactivate_wallet(self, council_id: int) -> bool:
        """
        Deactivate a wallet without deleting it.

        Parameters
        ----------
        council_id : int
            Council ID

        Returns
        -------
        bool
            True if deactivated, False if not found
        """
        result = await self.update_wallet(council_id=council_id, is_active=False)
        return result is not None

    async def activate_wallet(self, council_id: int) -> bool:
        """
        Activate a wallet.

        Parameters
        ----------
        council_id : int
            Council ID

        Returns
        -------
        bool
            True if activated, False if not found
        """
        result = await self.update_wallet(council_id=council_id, is_active=True)
        return result is not None


__all__ = ["WalletRepository"]

