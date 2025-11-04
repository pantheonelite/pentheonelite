"""Constants and utilities related to crypto analysts configuration."""

from app.backend.src.agents.agent_manager import AgentManager


def get_crypto_analyst_nodes():
    """Get crypto analyst nodes for workflow configuration."""
    return AgentManager.get_agent_nodes()


def get_crypto_agents_list():
    """Get the list of crypto agents for API responses."""
    return AgentManager.get_agents_list()


# Create CRYPTO_ANALYST_CONFIG from AgentManager for backward compatibility
def _build_analyst_config() -> dict:
    """
    Build analyst config from AgentManager.

    Returns
    -------
    dict
        Dictionary mapping agent keys to config dicts with 'agent_func' key.
    """
    config = {}
    for key, (node_name, func) in AgentManager.get_agent_nodes().items():
        config[key] = {"agent_func": func}
    return config


CRYPTO_ANALYST_CONFIG = _build_analyst_config()
