"""Service to load mock crypto council data with crypto-native agents."""

from decimal import Decimal
from typing import Any
import os

import structlog
from app.backend.client.aster import AsterClient
from app.backend.config.binance import BinanceConfig
from app.backend.db.repositories.council_repository import CouncilRepository
from app.backend.db.repositories.wallet_repository import WalletRepository
from app.backend.services.binance_futures_trading_service import BinanceFuturesTradingService
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.stdlib.get_logger(__name__)


class CryptoCouncilMockDataService:
    """Service for loading mock crypto council data with crypto-native agents."""

    WALLET_CONFIGS = [
        {
            "name": "hungcv",
            "exchange": "binance",
            "api_key": os.getenv("BINANCE_API_KEY_HUNGCV", ""),
            "secret_key": os.getenv("BINANCE_SECRET_KEY_HUNGCV", ""),
        },
        {
            "name": "hungnt",
            "exchange": "binance",
            "api_key": os.getenv("BINANCE_API_KEY_HUNGNT", ""),
            "secret_key": os.getenv("BINANCE_SECRET_KEY_HUNGNT", ""),
        }
    ]
    # Map display names to agent keys
    AGENT_NAME_TO_KEY = {
        "Satoshi Nakamoto": "satoshi_nakamoto",
        "Vitalik Buterin": "vitalik_buterin",
        "Michael Saylor": "michael_saylor",
        "CZ (Changpeng Zhao)": "cz_binance",
        "Elon Musk": "elon_musk",
        "DeFi Specialist": "defi_agent",
        "Crypto Technical Analyst": "crypto_technical",
        "Crypto Sentiment Analyst": "crypto_sentiment",
    }

    # Crypto council configurations with crypto-native agent combinations
    # Focused set of 5 diverse councils, each with unique agent combinations
    # All councils are system councils using pre-developed agent classes
    CRYPTO_COUNCIL_CONFIGS = [
        {
            "name": "Crypto Pantheon Elite",
            "description": "The flagship council combining Bitcoin's vision, Ethereum's innovation, and institutional adoption strategy. A balanced approach to crypto markets with focus on established assets and long-term value.",
            "strategy": "Multi-strategy balanced consensus",
            "agent_keys": ["satoshi_nakamoto", "vitalik_buterin", "michael_saylor"],
            "performance_multiplier": 1.2,  # Strong balanced performance
            "is_default": True,
            "is_system": True,
            "is_active": True,
            "tags": ["balanced", "flagship", "top-performers"],
            "trading_mode": "paper",
            "trading_type": "futures",
            "wallet_name": "hungcv",
        },
        {
            "name": "Bitcoin Maximalists",
            "description": "Pure Bitcoin focus with institutional and exchange perspectives. Emphasizes sound money principles, corporate treasury adoption, and Bitcoin's dominance in crypto markets.",
            "strategy": "Bitcoin-first high conviction",
            "agent_keys": ["satoshi_nakamoto", "michael_saylor", "cz_binance"],
            "performance_multiplier": 1.15,  # Strong BTC-focused performance
            "is_system": True,
            "is_active": True,
            "tags": ["bitcoin", "conservative", "institutional"],
            "trading_mode": "paper",
            "trading_type": "futures",
            "wallet_name": "hungnt",
        },
        # {
        #     "name": "DeFi Innovators",
        #     "description": "Specializes in decentralized finance protocols, smart contract platforms, and yield opportunities. Combines Ethereum ecosystem expertise with technical analysis and DeFi protocol evaluation.",
        #     "strategy": "DeFi protocol analysis and optimization",
        #     "agent_keys": ["vitalik_buterin", "defi_agent", "crypto_technical"],
        #     "performance_multiplier": 1.25,  # High performance in DeFi bull markets
        #     "is_system": True,
        #     "is_active": True,
        #     "tags": ["defi", "ethereum", "high-risk-high-reward"],    
        # },
        # {
        #     "name": "Data-Driven Quants",
        #     "description": "Pure quantitative approach using on-chain metrics, technical indicators, and sentiment analysis. Removes emotion from trading with data-backed decisions and risk management.",
        #     "strategy": "Quantitative technical analysis",
        #     "agent_keys": ["crypto_technical", "crypto_sentiment", "cz_binance"],
        #     "performance_multiplier": 1.05,  # Consistent moderate performance
        #     "is_system": True,
        #     "is_active": True,
        #     "tags": ["technical", "data-driven", "quantitative"],
        # },
        # {
        #     "name": "Viral Sentiment Council",
        #     "description": "Capitalizes on social sentiment, meme culture, and viral market movements. Combines Elon's influence tracking with sentiment analysis, balanced by Bitcoin fundamentals for risk management.",
        #     "strategy": "Social sentiment and viral trends",
        #     "agent_keys": ["elon_musk", "crypto_sentiment", "satoshi_nakamoto"],
        #     "performance_multiplier": 0.98,  # Volatile but captures momentum
        #     "is_system": True,
        #     "is_active": True,
        #     "tags": ["meme", "sentiment", "high-volatility"],
        # },
        # {
        #     "name": "Layer2 Scalability Council",
        #     "description": "Focus on L2 ecosystems, throughput improvements, and fee compression economics. Balances Ethereum core perspective with technical analytics and exchange microstructure.",
        #     "strategy": "L2 rotation with risk-adjusted entries",
        #     "agent_keys": ["vitalik_buterin", "crypto_technical", "cz_binance"],
        #     "performance_multiplier": 1.1,
        #     "is_system": True,
        #     "is_active": True,
        #     "tags": ["layer2", "ethereum", "scalability"],
        # },
        # {
        #     "name": "Altseason Momentum",
        #     "description": "Captures cross-chain alt momentum using sentiment bursts and TA confirmations, constrained by BTC dominance signals.",
        #     "strategy": "Momentum with BTC-dominance guardrails",
        #     "agent_keys": ["crypto_sentiment", "crypto_technical", "satoshi_nakamoto"],
        #     "performance_multiplier": 1.18,
        #     "is_system": True,
        #     "is_active": True,
        #     "tags": ["momentum", "alts", "risk-managed"],
        # },
        # {
        #     "name": "Institutional Macro Council",
        #     "description": "Macro-first council blending institutional treasury thinking, exchange flows, and BTC/ETH cycles.",
        #     "strategy": "Macro cycle positioning with staged entries",
        #     "agent_keys": ["michael_saylor", "cz_binance", "crypto_technical"],
        #     "performance_multiplier": 1.07,
        #     "is_system": True,
        #     "is_active": True,
        #     "tags": ["macro", "institutional", "btc_eth"],
        # },
        # {
        #     "name": "AI Narrative Hunters",
        #     "description": "Tracks AI x crypto narrative flows, focusing on compute, data markets, and inference credits with sentiment gating.",
        #     "strategy": "Narrative tracking with breakout confirmation",
        #     "agent_keys": ["elon_musk", "crypto_sentiment", "crypto_technical"],
        #     "performance_multiplier": 1.12,
        #     "is_system": True,
        #     "is_active": True,
        #     "tags": ["ai", "narratives", "breakouts"],
        # },
        # {
        #     "name": "Stable Yield Synth Council",
        #     "description": "Targets stablecoin and DeFi base yields, optimizing for safety, slippage, and protocol risk rotation.",
        #     "strategy": "Delta-neutral yield aggregation",
        #     "agent_keys": ["defi_agent", "crypto_technical", "cz_binance"],
        #     "performance_multiplier": 1.02,
        #     "is_system": True,
        #     "is_active": True,
        #     "tags": ["yield", "stablecoins", "defi"],
        # },
    ]

    # Note: Agent implementations are in app/backend/src/agents/crypto/
    # The agent_keys above map directly to these implementations via AgentRegistry

    # Mock debate scenarios for crypto
    # Note: agent names are kept as display names for readability in debates
    # These will be stored as-is in the database for display purposes

    @staticmethod
    async def create_wallets_for_councils(
        session: AsyncSession, council_configs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Create wallets for all council configurations.

        Parameters
        ----------
        session : AsyncSession
            Database session
        council_configs : list[dict[str, Any]]
            List of council configurations

        Returns
        -------
        dict[str, Any]
            Dictionary mapping council name to wallet object
        """
        import secrets

        wallet_repo = WalletRepository(session)
        wallets_by_council_name: dict[str, Any] = {}

        logger.info("Creating wallets for crypto councils...")

        for council_config in council_configs:
            council_name = council_config["name"]
            mock_ca = f"0x{secrets.token_hex(20)}"  # Random Ethereum-style address

            # Get exchange from config or default to "binance"
            exchange = council_config.get("exchange", "binance")

            
            # Get API credentials from config or use defaults
            api_key = council_config["api_key"]
            secret_key = council_config["secret_key"]

            # Get wallet name from config or use council name as default
            wallet_name = council_config.get("wallet_name", council_name)

            # Create wallet without council_id
            wallet = await wallet_repo.create_wallet_without_council(
                exchange=exchange,
                api_key=api_key,
                secret_key=secret_key,
                name=wallet_name,
                ca=mock_ca,
                is_active=True,
            )

            wallets_by_council_name[council_name] = wallet

            logger.info(
                "Created wallet for council %s: wallet_id=%d, exchange=%s",
                council_name,
                wallet.id,
                exchange,
            )

        await session.commit()
        logger.info("✓ All wallets created successfully")

        return wallets_by_council_name

    @staticmethod
    async def fetch_balance_from_api(wallet: Any) -> tuple[Decimal, Decimal]:
        """
        Fetch account balance from API based on wallet exchange type.

        Parameters
        ----------
        wallet : Any
            Wallet object with api_key, secret_key, and exchange

        Returns
        -------
        tuple[Decimal, Decimal]
            Tuple of (total_account_value, available_balance)
        """
        default_balance = Decimal("1000.0")
        total_account_value = default_balance
        available_balance = default_balance

        if not wallet.api_key or not wallet.secret_key:
            logger.info("No API credentials for wallet, using default balance")
            return total_account_value, available_balance

        try:
            exchange = wallet.exchange.lower() if wallet.exchange else "binance"

            if exchange == "binance":
                # Create Binance config from wallet credentials
                binance_config = BinanceConfig(
                    api_key=wallet.api_key,
                    api_secret=wallet.secret_key,
                    testnet=True,  # Paper trading uses testnet
                )

                # Create trading service and fetch balance
                trading_service = BinanceFuturesTradingService(config=binance_config)
                balance_info = await trading_service.aget_account_balance()

                total_account_value = Decimal(str(balance_info["total_balance"]))
                available_balance = Decimal(str(balance_info["available_balance"]))

                logger.info(
                    "Fetched Binance balance from API: total=%s, available=%s",
                    total_account_value,
                    available_balance,
                )
            elif exchange == "aster":
                # Create Aster client from wallet credentials
                aster_client = AsterClient(
                    api_key=wallet.api_key,
                    api_secret=wallet.secret_key,
                )

                # Fetch account info from Aster API
                account_info = await aster_client.aget_account_info()

                total_account_value = Decimal(str(account_info.total_balance))
                available_balance = Decimal(str(account_info.available_balance))

                logger.info(
                    "Fetched Aster balance from API: total=%s, available=%s",
                    total_account_value,
                    available_balance,
                )
            else:
                logger.warning(
                    "Unknown exchange type '%s' for wallet, using default balance",
                    exchange,
                )
        except Exception as e:
            logger.warning(
                "Failed to fetch balance from API (exchange: %s), using default: %s",
                wallet.exchange,
                e,
            )
            # Fallback to default balance
            total_account_value = default_balance
            available_balance = default_balance

        return total_account_value, available_balance

    @staticmethod
    async def load_crypto_mock_data(session: AsyncSession, replace_existing: bool = False) -> bool:
        """
        Load mock crypto council data.

        Parameters
        ----------
        session : AsyncSession
            Database session
        replace_existing : bool
            If True, replace existing crypto councils. If False, skip if they exist.

        Returns
        -------
        bool
            True if data was loaded, False if skipped
        """
        try:
            # Check if crypto councils exist
            repo = CouncilRepository(session)
            existing_councils = await repo.get_all_councils()
            expected_names = {config["name"] for config in CryptoCouncilMockDataService.CRYPTO_COUNCIL_CONFIGS}
            existing_names = {council.name for council in existing_councils}
            crypto_councils_exist = any(name in existing_names for name in expected_names)

            if crypto_councils_exist and not replace_existing:
                logger.info("Crypto councils already exist, skipping mock data load")
                return False

            if replace_existing and crypto_councils_exist:
                logger.info("Replacing existing crypto councils...")
                # Delete only crypto councils
                from sqlalchemy import text

                for name in expected_names:
                    await session.execute(text("DELETE FROM councils WHERE name = :name"), {"name": name})
                await session.commit()

            logger.info("Loading crypto council mock data...")

            # Step 1: Create all wallets first
            wallets_by_council_name = await CryptoCouncilMockDataService.create_wallets_for_councils(
                session, CryptoCouncilMockDataService.WALLET_CONFIGS
            )

            # Step 2: Create all crypto councils and link to wallets
            repo = CouncilRepository(session)

            for council_config in CryptoCouncilMockDataService.CRYPTO_COUNCIL_CONFIGS:
                # Build agents JSONB structure for system councils
                agents_jsonb = {
                    "agents": [
                        {
                            "agent_key": agent_key,
                            "role": "analyst",
                        }
                        for agent_key in council_config["agent_keys"]
                    ]
                }

                # Build connections JSONB structure
                # Simple sequential flow: all agents → portfolio_manager
                connections_jsonb = {
                    "edges": [
                        {
                            "source": agent_key,
                            "target": "portfolio_manager",
                        }
                        for agent_key in council_config["agent_keys"]
                    ]
                }

                # Get wallet for this council (created in previous step)
                council_name = council_config["name"]
                wallet_name = council_config.get("wallet_name", council_name)
                wallet = wallets_by_council_name.get(wallet_name)

                if not wallet:
                    logger.warning(
                        "No wallet found for council %s, skipping wallet linking",
                        council_name,
                    )

                # Now create council with wallet_id
                council = await repo.create_council(
                    name=council_config["name"],
                    agents=agents_jsonb,
                    connections=connections_jsonb,
                    user_id=None,  # System council
                    description=council_config["description"],
                    strategy=council_config["strategy"],
                    tags=council_config.get("tags", []),
                    workflow_config={},
                    visual_layout=None,
                    initial_capital=1000.0,
                    risk_settings=None,
                    is_system=council_config.get("is_system", False),
                    is_public=council_config.get("is_public", True),
                    is_template=False,
                    forked_from_id=None,
                    trading_mode=council_config.get("trading_mode", "paper"),
                    trading_type=council_config.get("trading_type", "futures"),
                )

                # Fetch balance from API if wallet is available
                if wallet:
                    total_account_value, available_balance = await CryptoCouncilMockDataService.fetch_balance_from_api(
                        wallet
                    )
                    council.total_account_value = total_account_value
                    council.available_balance = available_balance
                    council.initial_capital = total_account_value

                    # Link wallet_id to council
                    council.wallet_id = wallet.id

                    logger.info(
                        "Set balance for council %s: total=%s, available=%s, wallet_id=%d",
                        council.name,
                        total_account_value,
                        available_balance,
                        wallet.id,
                    )
                else:
                    # Default balance if no wallet
                    default_balance = Decimal("1000.0")
                    council.total_account_value = default_balance
                    council.available_balance = default_balance
                    council.initial_capital = default_balance
                    logger.info(
                        "No wallet for council %s, using default balance",
                        council.name,
                    )
                
                if council_config.get("is_active"):
                    council.is_active = True
                
                await session.commit()
                await session.refresh(council)
                
                wallet_id = wallet.id if wallet else None
                logger.info(
                    "Created crypto council: %s (ID: %d) with agent_keys: %s and wallet (ID: %s)",
                    council.name,
                    council.id,
                    council_config["agent_keys"],
                    wallet_id,
                )

                # TODO: Add debate messages, market orders, and performance snapshots
                # These require additional repository methods that will be added later

            logger.info("✓ Crypto council mock data loaded successfully")
            return True

        except Exception as e:
            logger.exception("Error loading crypto council mock data: %s", e)
            return False


async def load_crypto_council_mock_data(session: AsyncSession) -> None:
    """Public function to load crypto council mock data."""
    await CryptoCouncilMockDataService.load_crypto_mock_data(session)
