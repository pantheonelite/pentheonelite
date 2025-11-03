"""Agent metadata registry and helpers.

Defines a structured representation for council agent metadata and exposes a
central registry consumable by routers and services.
"""

from dataclasses import dataclass
from typing import Any

from app.backend.api.schemas import AgentInfo


@dataclass(frozen=True)
class AgentMetadata:
    """Structured metadata for a council agent.

    Parameters
    ----------
    name : str
        Human-friendly agent name.
    type : str
        Agent category/type identifier.
    traits : list[str]
        Highlighted traits or tags.
    specialty : str
        Primary area of expertise.
    system_prompt : str
        Canonical system prompt used to prime the agent.
    """

    name: str
    type: str
    traits: list[str]
    specialty: str
    system_prompt: str


AGENT_METADATA: dict[str, AgentMetadata] = {
    "satoshi_nakamoto": AgentMetadata(
        name="Satoshi Nakamoto",
        type="crypto_visionary",
        traits=["Decentralization", "Sound Money", "Privacy"],
        specialty="Bitcoin philosophy and decentralization",
        system_prompt=(
            "You are Satoshi Nakamoto, creator of Bitcoin, focusing on decentralization and sound money principles."
        ),
    ),
    "vitalik_buterin": AgentMetadata(
        name="Vitalik Buterin",
        type="ethereum_founder",
        traits=["Innovation", "Smart Contracts", "DeFi"],
        specialty="Ethereum ecosystem and smart contracts",
        system_prompt=("You are Vitalik Buterin, focusing on programmable blockchain and decentralized applications."),
    ),
    "defi_agent": AgentMetadata(
        name="DeFi Agent",
        type="analyst",
        traits=["DeFi", "Liquidity Pools", "Yield Farming"],
        specialty=("Decentralized finance protocols, DEXs, and yield strategies"),
        system_prompt=(
            "You are a DeFi-focused analyst covering AMMs, lending, liquid staking, and on-chain liquidity dynamics."
        ),
    ),
    "michael_saylor": AgentMetadata(
        name="Michael Saylor",
        type="institutional_advisor",
        traits=[
            "Corporate Strategy",
            "Store of Value",
            "Institutional Adoption",
        ],
        specialty=("Bitcoin as digital gold and corporate treasury"),
        system_prompt=("You are Michael Saylor, CEO of MicroStrategy, focusing on Bitcoin as a store of value."),
    ),
    "cz_binance": AgentMetadata(
        name="CZ (Changpeng Zhao)",
        type="exchange_expert",
        traits=["Market Efficiency", "Liquidity", "Trading"],
        specialty="Exchange dynamics and market structure",
        system_prompt=("You are CZ, founder of Binance, focusing on market efficiency and liquidity."),
    ),
    "elon_musk": AgentMetadata(
        name="Elon Musk",
        type="disruptor",
        traits=["Innovation", "Memes", "Social Impact"],
        specialty="Technology disruption and viral adoption",
        system_prompt=("You are Elon Musk, focusing on technological disruption and mass adoption."),
    ),
    "crypto_technical": AgentMetadata(
        name="Technical Analyst",
        type="technical_analyst",
        traits=["Technical Analysis", "Chart Patterns", "Indicators"],
        specialty="Technical analysis and chart patterns",
        system_prompt=("You are a technical analyst focusing on chart patterns and indicators."),
    ),
    "crypto_sentiment": AgentMetadata(
        name="Sentiment Analyst",
        type="sentiment_analyst",
        traits=["Social Media", "News", "Market Sentiment"],
        specialty="Market sentiment and social analysis",
        system_prompt=("You are a sentiment analyst focusing on social media and news sentiment."),
    ),
    "crypto_analyst": AgentMetadata(
        name="Crypto Analyst",
        type="fundamental_analyst",
        traits=["Fundamental Analysis", "On-chain Data", "Valuation"],
        specialty="Fundamental analysis and on-chain metrics",
        system_prompt=("You are a fundamental analyst focusing on on-chain data and valuation."),
    ),
}


def normalize_agent_list(raw_agents: list[dict] | dict | None) -> list[dict] | None:
    """Normalize agents payload from DB to a flat list if present.

    Parameters
    ----------
    raw_agents : list[dict] | dict | None
        Agents payload from DB; can be a list directly or a dict containing
        an "agents" key.

    Returns
    -------
    list[dict] | None
        A flat list of agent dicts if available, otherwise None.
    """
    if raw_agents is None:
        return None
    agents_data: Any = raw_agents
    if isinstance(agents_data, dict) and "agents" in agents_data:
        agents_data = agents_data["agents"]
    return agents_data if isinstance(agents_data, list) else None


def create_agent_info(agent_data: dict) -> AgentInfo:
    """Convert raw agent JSON into AgentInfo using registry metadata when available."""
    agent_key = agent_data.get("agent_key") or agent_data.get("id", "")
    meta = AGENT_METADATA.get(agent_key)

    name = meta.name if meta else agent_key.replace("_", " ").title()
    agent_type = meta.type if meta else "analyst"
    traits = meta.traits if meta else None
    specialty = meta.specialty if meta else None
    system_prompt = meta.system_prompt if meta else None

    return AgentInfo(
        id=agent_key,
        name=name,
        type=agent_type,
        role=agent_data.get("role", "analyst"),
        traits=traits,
        specialty=specialty,
        system_prompt=system_prompt,
        position=agent_data.get("position"),
    )
