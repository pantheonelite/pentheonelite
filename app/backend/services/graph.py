"""Graph service for creating and managing trading agent graphs."""

import asyncio
import json
import re

import structlog
from app.backend.services.agent_service import AgentService
from app.backend.src.agents.crypto_risk_manager import CryptoRiskManagerAgent
from app.backend.src.agents.portfolio_manager import CryptoPortfolioManagerAgent
from app.backend.src.graph.state import CryptoAgentState as AgentState
from app.backend.src.utils.analysts import CRYPTO_ANALYST_CONFIG
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

logger = structlog.get_logger(__name__)


def start(state: AgentState) -> AgentState:
    """
    Start node that initializes the agent state.

    Parameters
    ----------
    state : AgentState
        The current agent state.

    Returns
    -------
    AgentState
        The initialized state.
    """
    return state


class GraphService:
    """Service for creating and managing trading agent graphs."""

    def __init__(self):
        """Initialize the graph service."""
        self._graphs = {}
        self._agent_service = AgentService()

    def extract_base_agent_key(self, unique_id: str) -> str:
        """
        Extract the base agent key from a unique node ID.

        Parameters
        ----------
        unique_id : str
            The unique node ID with suffix (e.g., "warren_buffett_abc123" or "portfolio_manager_0")

        Returns
        -------
        str
            The base agent key (e.g., "warren_buffett" or "portfolio_manager")
        """
        # For agent nodes, remove the last underscore and suffix
        parts = unique_id.split("_")
        if len(parts) >= 2:
            last_part = parts[-1]
            # If the last part is a 6-character alphanumeric string or a numeric suffix, it's likely our suffix
            if (len(last_part) == 6 and re.match(r"^[a-z0-9]+$", last_part)) or last_part.isdigit():
                return "_".join(parts[:-1])
        return unique_id  # Return original if no suffix pattern found

    def create_graph(
        self, graph_nodes: list, graph_edges: list, graph_id: str | None = None, agent_instances: list | None = None
    ) -> StateGraph:
        """
        Create the workflow based on the React Flow graph structure.

        Parameters
        ----------
        graph_nodes : list
            List of graph nodes.
        graph_edges : list
            List of graph edges.
        graph_id : str | None
            Optional graph ID for tracking.
        agent_instances : list | None
            Optional list of agent instances to use (for system councils).
            If provided, uses these instead of CRYPTO_ANALYST_CONFIG.

        Returns
        -------
        StateGraph
            The created graph.
        """
        graph = StateGraph(AgentState)
        graph.add_node("start_node", start)

        # Extract agent IDs from graph structure
        # Nodes can be objects with .id or dicts with "id" or "agent_key"
        agent_ids = []
        for node in graph_nodes:
            if hasattr(node, "id"):
                agent_ids.append(node.id)
            elif isinstance(node, dict):
                agent_ids.append(node.get("id") or node.get("agent_key"))
            else:
                agent_ids.append(str(node))

        agent_ids_set = set(agent_ids)

        # Track which nodes are portfolio managers for special handling
        portfolio_manager_nodes = set()

        # If agent_instances provided, create mapping from agent_key to instance
        agent_instance_map = {}
        if agent_instances:
            for agent_instance in agent_instances:
                agent_instance_map[agent_instance.agent_id] = agent_instance
            logger.info(
                "Using provided agent instances",
                agent_count=len(agent_instances),
                agent_keys=list(agent_instance_map.keys()),
            )

        # Add agent nodes
        for graph_node in graph_nodes:
            # Extract unique agent ID
            if hasattr(graph_node, "id"):
                unique_agent_id = graph_node.id
            elif isinstance(graph_node, dict):
                unique_agent_id = graph_node.get("id") or graph_node.get("agent_key")
            else:
                unique_agent_id = str(graph_node)

            base_agent_key = self.extract_base_agent_key(unique_agent_id)

            # Track portfolio manager nodes for special handling
            if base_agent_key == "portfolio_manager":
                portfolio_manager_nodes.add(unique_agent_id)
                continue

            # If using agent instances, create node from instance
            if agent_instances:
                # Extract the base agent key from the node (without numeric suffix)
                agent_key = graph_node.get("data", {}).get("agent_key") if isinstance(graph_node, dict) else None
                if not agent_key:
                    # Try to extract from node ID
                    agent_key = base_agent_key

                if agent_key in agent_instance_map:
                    agent_instance = agent_instance_map[agent_key]

                    # Create a wrapper function that calls run_agent
                    def create_agent_wrapper(instance):
                        def agent_wrapper(state):
                            return instance.run_agent(state)

                        return agent_wrapper

                    agent_function = create_agent_wrapper(agent_instance)
                    graph.add_node(unique_agent_id, agent_function)
                    logger.debug(
                        "Added agent node from instance",
                        node_id=unique_agent_id,
                        agent_key=agent_key,
                    )
                else:
                    logger.warning(
                        "Agent instance not found for node",
                        node_id=unique_agent_id,
                        agent_key=agent_key,
                    )
                    continue
            else:
                # Fall back to CRYPTO_ANALYST_CONFIG (old behavior)
                if base_agent_key not in CRYPTO_ANALYST_CONFIG:
                    logger.warning(
                        "Agent not found in CRYPTO_ANALYST_CONFIG",
                        node_id=unique_agent_id,
                        base_agent_key=base_agent_key,
                    )
                    continue

                analyst_nodes = {
                    key: (f"{key}_agent", config["agent_func"]) for key, config in CRYPTO_ANALYST_CONFIG.items()
                }
                _, node_func = analyst_nodes[base_agent_key]
                agent_function = self._agent_service.create_agent_function(node_func, unique_agent_id)
                graph.add_node(unique_agent_id, agent_function)

        # Add portfolio manager nodes and their corresponding risk managers
        risk_manager_nodes = {}  # Map portfolio manager ID to risk manager ID
        for portfolio_manager_id in portfolio_manager_nodes:
            # Create portfolio manager agent instance
            portfolio_manager_agent = CryptoPortfolioManagerAgent()
            portfolio_manager_function = self._agent_service.create_agent_function(
                portfolio_manager_agent.arun_agent, portfolio_manager_id
            )
            graph.add_node(portfolio_manager_id, portfolio_manager_function)

            # Create unique risk manager for this portfolio manager
            suffix = portfolio_manager_id.split("_")[-1]
            risk_manager_id = f"risk_management_agent_{suffix}"
            risk_manager_nodes[portfolio_manager_id] = risk_manager_id

            # Create risk manager agent instance
            risk_manager_agent = CryptoRiskManagerAgent()
            risk_manager_function = self._agent_service.create_agent_function(
                risk_manager_agent.arun_agent, risk_manager_id
            )
            graph.add_node(risk_manager_id, risk_manager_function)

        # Build connections based on React Flow graph structure
        nodes_with_incoming_edges = set()
        nodes_with_outgoing_edges = set()
        direct_to_portfolio_managers = {}  # Map analyst ID to portfolio manager ID for direct connections

        for edge in graph_edges:
            # Extract source and target from edge (handle both dict and object format)
            edge_source = edge.get("source") if isinstance(edge, dict) else edge.source
            edge_target = edge.get("target") if isinstance(edge, dict) else edge.target

            # Only consider edges between agent nodes (not from stock tickers)
            if edge_source in agent_ids_set and edge_target in agent_ids_set:
                source_base_key = self.extract_base_agent_key(edge_source)
                target_base_key = self.extract_base_agent_key(edge_target)

                nodes_with_incoming_edges.add(edge_target)
                nodes_with_outgoing_edges.add(edge_source)

                # Check if this is a direct connection from analyst to portfolio manager
                is_analyst_to_portfolio = (
                    target_base_key == "portfolio_manager" and source_base_key != "portfolio_manager"
                )

                # For agent instances, check if source is an analyst agent
                if agent_instances and is_analyst_to_portfolio:
                    # Don't add direct edge to portfolio manager - we'll route through risk manager
                    direct_to_portfolio_managers[edge_source] = edge_target
                elif not agent_instances and (
                    source_base_key in CRYPTO_ANALYST_CONFIG
                    and source_base_key != "portfolio_manager"
                    and target_base_key == "portfolio_manager"
                ):
                    # Old behavior: check against CRYPTO_ANALYST_CONFIG
                    direct_to_portfolio_managers[edge_source] = edge_target
                else:
                    # Add edge between agent nodes (but not direct to portfolio managers)
                    graph.add_edge(edge_source, edge_target)

        # Connect start_node to nodes that don't have incoming edges from other agents
        for agent_id in agent_ids:
            if agent_id not in nodes_with_incoming_edges:
                base_agent_key = self.extract_base_agent_key(agent_id)
                # Skip portfolio managers
                if base_agent_key == "portfolio_manager":
                    continue
                # Add edge from start_node
                if agent_instances or base_agent_key in CRYPTO_ANALYST_CONFIG:
                    graph.add_edge("start_node", agent_id)

        # Connect analysts that have direct connections to portfolio managers to their corresponding risk managers
        for analyst_id, portfolio_manager_id in direct_to_portfolio_managers.items():
            risk_manager_id = risk_manager_nodes[portfolio_manager_id]
            graph.add_edge(analyst_id, risk_manager_id)

        # Connect each risk manager to its corresponding portfolio manager
        for portfolio_manager_id, risk_manager_id in risk_manager_nodes.items():
            graph.add_edge(risk_manager_id, portfolio_manager_id)

        # Connect portfolio managers to END
        for portfolio_manager_id in portfolio_manager_nodes:
            graph.add_edge(portfolio_manager_id, END)

        # Set the entry point to the start node
        graph.set_entry_point("start_node")

        # Store graph if ID provided
        if graph_id:
            self._graphs[graph_id] = graph

        return graph

    def get_graph(self, graph_id: str) -> StateGraph | None:
        """
        Get a graph by ID.

        Parameters
        ----------
        graph_id : str
            The graph ID.

        Returns
        -------
        StateGraph | None
            The graph if found, None otherwise.
        """
        return self._graphs.get(graph_id)

    def list_graphs(self) -> list[str]:
        """
        List all graph IDs.

        Returns
        -------
        list[str]
            List of graph IDs.
        """
        return list(self._graphs.keys())

    def delete_graph(self, graph_id: str) -> bool:
        """
        Delete a graph by ID.

        Parameters
        ----------
        graph_id : str
            The graph ID.

        Returns
        -------
        bool
            True if deleted, False if not found.
        """
        if graph_id in self._graphs:
            del self._graphs[graph_id]
            return True
        return False

    async def arun_graph(
        self,
        graph: StateGraph,
        portfolio: dict,
        tickers: list[str],
        start_date: str,
        end_date: str,
        model_name: str,
        model_provider: str,
        request=None,
    ) -> dict:
        """
        Async wrapper for run_graph to work with asyncio.

        Parameters
        ----------
        graph : StateGraph
            The graph to run.
        portfolio : dict
            The portfolio state.
        tickers : list[str]
            List of tickers.
        start_date : str
            Start date.
        end_date : str
            End date.
        model_name : str
            Model name.
        model_provider : str
            Model provider.
        request : Any
            Request object.

        Returns
        -------
        dict
            Graph execution result.
        """
        # Use run_in_executor to run the synchronous function in a separate thread
        # so it doesn't block the event loop
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.run_graph(
                graph, portfolio, tickers, start_date, end_date, model_name, model_provider, request
            ),
        )  # Use default executor

    def run_graph(
        self,
        graph: StateGraph,
        portfolio: dict,
        tickers: list[str],
        start_date: str,
        end_date: str,
        model_name: str,
        model_provider: str,
        request=None,
    ) -> dict:
        """
        Run the graph with the given portfolio, tickers,
        start date, end date, show reasoning, model name,
        and model provider.

        Parameters
        ----------
        graph : StateGraph
            The graph to run.
        portfolio : dict
            The portfolio state.
        tickers : list[str]
            List of tickers.
        start_date : str
            Start date.
        end_date : str
            End date.
        model_name : str
            Model name.
        model_provider : str
            Model provider.
        request : Any
            Request object.

        Returns
        -------
        dict
            Graph execution result.
        """
        # Compile the graph before invoking
        compiled_graph = graph.compile()

        return compiled_graph.invoke(
            {
                "messages": [
                    HumanMessage(
                        content="Make trading decisions based on the provided data.",
                    )
                ],
                "data": {
                    "symbols": tickers,
                    "tickers": tickers,
                    "portfolio": portfolio,
                    "start_date": start_date,
                    "end_date": end_date,
                    "analyst_signals": {},
                },
                "metadata": {
                    "show_reasoning": True,
                    "model_name": model_name,
                    "model_provider": model_provider,
                    "request": request,  # Pass the request for agent-specific model access
                },
            },
        )

    def parse_hedge_fund_response(self, response: str) -> dict | None:
        """
        Parse a JSON string and return a dictionary.

        Parameters
        ----------
        response : str
            The JSON response string.

        Returns
        -------
        dict | None
            Parsed dictionary or None if parsing fails.
        """
        try:
            return json.loads(response)
        except json.JSONDecodeError as exc:
            logger.info(
                "JSON decoding error",
                error=str(exc),
                response=response,
            )
            return None
        except TypeError as exc:
            logger.info(
                "Invalid response type",
                expected_type="str",
                actual_type=type(response).__name__,
                error=str(exc),
            )
            return None
        except Exception as exc:
            logger.info(
                "Unexpected error while parsing response",
                error=str(exc),
                response=response,
            )
            return None
