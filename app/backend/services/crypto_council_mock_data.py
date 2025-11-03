"""Service to load mock crypto council data with crypto-native agents."""

from decimal import Decimal
from typing import Any, ClassVar

import structlog
from app.backend.db.repositories.council_repository import CouncilRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.stdlib.get_logger(__name__)


class CryptoCouncilMockDataService:
    """Service for loading mock crypto council data with crypto-native agents."""

    # Map display names to agent keys
    AGENT_NAME_TO_KEY: ClassVar[dict[str, str]] = {
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
    CRYPTO_COUNCIL_CONFIGS: ClassVar[list[dict[str, Any]]] = [
        {
            "name": "Crypto Pantheon Elite",
            "description": (
                "The flagship council combining Bitcoin's vision, Ethereum's innovation, "
                "and institutional adoption strategy. A balanced approach to crypto markets "
                "with focus on established assets and long-term value."
            ),
            "strategy": "Multi-strategy balanced consensus",
            "agent_keys": ["satoshi_nakamoto", "vitalik_buterin", "michael_saylor"],
            "performance_multiplier": 1.2,  # Strong balanced performance
            "is_default": True,
            "is_system": True,
            "is_active": True,
            "tags": ["balanced", "flagship", "top-performers"],
        },
        {
            "name": "Bitcoin Maximalists",
            "description": (
                "Pure Bitcoin focus with institutional and exchange perspectives. "
                "Emphasizes sound money principles, corporate treasury adoption, "
                "and Bitcoin's dominance in crypto markets."
            ),
            "strategy": "Bitcoin-first high conviction",
            "agent_keys": ["satoshi_nakamoto", "michael_saylor", "cz_binance"],
            "performance_multiplier": 1.15,  # Strong BTC-focused performance
            "is_system": True,
            "is_active": True,
            "tags": ["bitcoin", "conservative", "institutional"],
        },
        {
            "name": "DeFi Innovators",
            "description": (
                "Specializes in decentralized finance protocols, smart contract platforms, "
                "and yield opportunities. Combines Ethereum ecosystem expertise with "
                "technical analysis and DeFi protocol evaluation."
            ),
            "strategy": "DeFi protocol analysis and optimization",
            "agent_keys": ["vitalik_buterin", "defi_agent", "crypto_technical"],
            "performance_multiplier": 1.25,  # High performance in DeFi bull markets
            "is_system": True,
            "is_active": True,
            "tags": ["defi", "ethereum", "high-risk-high-reward"],
        },
        {
            "name": "Data-Driven Quants",
            "description": (
                "Pure quantitative approach using on-chain metrics, technical indicators, "
                "and sentiment analysis. Removes emotion from trading with data-backed "
                "decisions and risk management."
            ),
            "strategy": "Quantitative technical analysis",
            "agent_keys": ["crypto_technical", "crypto_sentiment", "cz_binance"],
            "performance_multiplier": 1.05,  # Consistent moderate performance
            "is_system": True,
            "is_active": True,
            "tags": ["technical", "data-driven", "quantitative"],
        },
        {
            "name": "Viral Sentiment Council",
            "description": (
                "Capitalizes on social sentiment, meme culture, and viral market movements. "
                "Combines Elon's influence tracking with sentiment analysis, balanced by "
                "Bitcoin fundamentals for risk management."
            ),
            "strategy": "Social sentiment and viral trends",
            "agent_keys": ["elon_musk", "crypto_sentiment", "satoshi_nakamoto"],
            "performance_multiplier": 0.98,  # Volatile but captures momentum
            "is_system": True,
            "is_active": True,
            "tags": ["meme", "sentiment", "high-volatility"],
        },
        {
            "name": "Layer2 Scalability Council",
            "description": (
                "Focus on L2 ecosystems, throughput improvements, and fee compression economics. "
                "Balances Ethereum core perspective with technical analytics and exchange microstructure."
            ),
            "strategy": "L2 rotation with risk-adjusted entries",
            "agent_keys": ["vitalik_buterin", "crypto_technical", "cz_binance"],
            "performance_multiplier": 1.1,
            "is_system": True,
            "is_active": True,
            "tags": ["layer2", "ethereum", "scalability"],
        },
        {
            "name": "Altseason Momentum",
            "description": (
                "Captures cross-chain alt momentum using sentiment bursts and TA confirmations, "
                "constrained by BTC dominance signals."
            ),
            "strategy": "Momentum with BTC-dominance guardrails",
            "agent_keys": ["crypto_sentiment", "crypto_technical", "satoshi_nakamoto"],
            "performance_multiplier": 1.18,
            "is_system": True,
            "is_active": True,
            "tags": ["momentum", "alts", "risk-managed"],
        },
        {
            "name": "Institutional Macro Council",
            "description": (
                "Macro-first council blending institutional treasury thinking, exchange flows, and BTC/ETH cycles."
            ),
            "strategy": "Macro cycle positioning with staged entries",
            "agent_keys": ["michael_saylor", "cz_binance", "crypto_technical"],
            "performance_multiplier": 1.07,
            "is_system": True,
            "is_active": True,
            "tags": ["macro", "institutional", "btc_eth"],
        },
        {
            "name": "AI Narrative Hunters",
            "description": (
                "Tracks AI x crypto narrative flows, focusing on compute, data markets, "
                "and inference credits with sentiment gating."
            ),
            "strategy": "Narrative tracking with breakout confirmation",
            "agent_keys": ["elon_musk", "crypto_sentiment", "crypto_technical"],
            "performance_multiplier": 1.12,
            "is_system": True,
            "is_active": True,
            "tags": ["ai", "narratives", "breakouts"],
        },
        {
            "name": "Stable Yield Synth Council",
            "description": (
                "Targets stablecoin and DeFi base yields, optimizing for safety, slippage, and protocol risk rotation."
            ),
            "strategy": "Delta-neutral yield aggregation",
            "agent_keys": ["defi_agent", "crypto_technical", "cz_binance"],
            "performance_multiplier": 1.02,
            "is_system": True,
            "is_active": True,
            "tags": ["yield", "stablecoins", "defi"],
        },
    ]

    # Note: Agent implementations are in app/backend/src/agents/crypto/
    # The agent_keys above map directly to these implementations via AgentRegistry

    # Mock debate scenarios for crypto
    # Note: agent names are kept as display names for readability in debates
    # These will be stored as-is in the database for display purposes

    @staticmethod
    async def load_crypto_mock_data(
        session: AsyncSession, replace_existing: bool = False, count: int | None = None
    ) -> bool:
        """
        Load mock crypto council data.

        Parameters
        ----------
        session : AsyncSession
            Database session
        replace_existing : bool
            If True, replace existing crypto councils. If False, skip if they exist.
        count : int | None
            Number of councils to load. If None, loads all available councils.

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

            # Determine which councils to load
            councils_to_load = CryptoCouncilMockDataService.CRYPTO_COUNCIL_CONFIGS
            if count is not None:
                if count <= 0:
                    logger.warning("Invalid count: %d. Loading all councils.", count)
                elif count > len(councils_to_load):
                    logger.warning(
                        "Requested count %d exceeds available councils (%d). Loading all councils.",
                        count,
                        len(councils_to_load),
                    )
                else:
                    councils_to_load = councils_to_load[:count]
                    logger.info(
                        "Loading %d out of %d available councils",
                        count,
                        len(CryptoCouncilMockDataService.CRYPTO_COUNCIL_CONFIGS),
                    )

            logger.info("Loading crypto council mock data...")

            # Create selected crypto councils
            repo = CouncilRepository(session)
            for council_config in councils_to_load:
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
                )

                # Set trading modes for new position-based system
                council.trading_mode = "paper"  # Binance Testnet
                council.trading_type = "futures"  # Leveraged positions
                council.total_account_value = Decimal("1000.0")
                council.available_balance = Decimal("1000.0")

                # Update is_active if specified
                if council_config.get("is_active"):
                    council.is_active = True
                    await session.commit()
                    await session.refresh(council)

                logger.info(
                    "Created crypto council: %s (ID: %d) with agent_keys: %s",
                    council.name,
                    council.id,
                    council_config["agent_keys"],
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
