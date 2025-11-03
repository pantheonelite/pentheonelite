"""Centralized tool management for crypto trading workflow nodes."""

import asyncio
import concurrent.futures
import json
from typing import Any

import structlog
from app.backend.src.tools.crypto import (
    aster_get_history,
    aster_get_price,
    technical_indicators_analysis,
    trading_strategy_analysis,
    volume_analysis,
)
from app.backend.src.tools.web import (
    crypto_news_search,
    crypto_web_sentiment,
    duckduckgo_web_search,
    rss_news_feed,
)

logger = structlog.get_logger(__name__)


class ToolManager:
    """
    Centralized tool management for crypto trading workflow nodes.

    This class provides:
    - Lazy initialization of tools
    - Consistent error handling
    - Symbol processing utilities
    - Agent management
    """

    def __init__(self):
        """Initialize the tool manager with lazy loading."""
        self._tools: dict[str, Any] = {}
        self._agents: dict[str, Any] = {}

    def get_tool(self, tool_name: str) -> Any:
        """
        Get a tool instance with lazy initialization.

        Parameters
        ----------
        tool_name : str
            Name of the tool to get

        Returns
        -------
        Any
            Tool instance
        """
        if tool_name not in self._tools:
            self._tools[tool_name] = self._create_tool(tool_name)
        return self._tools[tool_name]

    def get_agent(self, agent_name: str) -> Any:
        """
        Get an agent instance with lazy initialization.

        Parameters
        ----------
        agent_name : str
            Name of the agent to get

        Returns
        -------
        Any
            Agent instance
        """
        if agent_name not in self._agents:
            self._agents[agent_name] = self._create_agent(agent_name)
        return self._agents[agent_name]

    def _create_tool(self, tool_name: str) -> Any:
        """Get a @tool decorator function based on the tool name."""
        tool_map = {
            "duckduckgo_search": duckduckgo_web_search,
            "aster_price": aster_get_price,
            "aster_history": aster_get_history,
            "technical_indicators": technical_indicators_analysis,
            "trading_strategy": trading_strategy_analysis,
            "volume_analysis": volume_analysis,
            "crypto_news_search": crypto_news_search,
            "crypto_web_sentiment": crypto_web_sentiment,
            "rss_news_feed": rss_news_feed,
        }

        tool_or_class = tool_map.get(tool_name)
        if not tool_or_class:
            raise ValueError(f"Unknown tool: {tool_name}")

        # All tools are now @tool decorator functions, return them directly
        return tool_or_class

    def _create_agent(self, agent_name: str) -> Any:
        """Create an agent instance based on the agent name."""
        # Use dynamic imports to avoid circular imports
        agent_map = {
            "crypto_analyst": "app.backend.src.agents.analyst.crypto_analyst.CryptoAnalystAgent",
            "crypto_sentiment": "app.backend.src.agents.analyst.crypto_sentiment.CryptoSentimentAgent",
            "crypto_technical": "app.backend.src.agents.analyst.crypto_technical.CryptoTechnicalAgent",
            "crypto_risk_manager": "app.backend.src.agents.crypto_risk_manager.CryptoRiskManagerAgent",
            "portfolio_manager": "app.backend.src.agents.portfolio_manager.CryptoPortfolioManagerAgent",
            # Persona agents
            "cz_binance": "app.backend.src.agents.analyst.cz_binance.CZBinanceAgent",
            "vitalik_buterin": "app.backend.src.agents.analyst.vitalik_buterin.VitalikButerinAgent",
            "michael_saylor": "app.backend.src.agents.analyst.michael_saylor.MichaelSaylorAgent",
            "satoshi_nakamoto": "app.backend.src.agents.analyst.satoshi_nakamoto.SatoshiNakamotoAgent",
            "elon_musk": "app.backend.src.agents.analyst.elon_musk.ElonMuskAgent",
        }

        agent_module_path = agent_map.get(agent_name)
        if not agent_module_path:
            raise ValueError(f"Unknown agent: {agent_name}")

        try:
            # Dynamic import to avoid circular imports
            module_path, class_name = agent_module_path.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            return agent_class()
        except Exception:
            logger.exception("Failed to create agent %s", agent_name)
            raise

    @staticmethod
    def clean_symbol(symbol: str) -> str:
        """
        Clean and normalize a trading symbol.

        Parameters
        ----------
        symbol : str
            Raw trading symbol

        Returns
        -------
        str
            Cleaned symbol
        """
        return symbol.replace("/", "").replace("USDT", "").replace("/", "").strip()

    @staticmethod
    def to_aster_symbol(symbol: str) -> str:
        """
        Convert symbol to Aster API format.

        Parameters
        ----------
        symbol : str
            Trading symbol

        Returns
        -------
        str
            Aster-formatted symbol
        """
        cleaned = ToolManager.clean_symbol(symbol)
        return f"{cleaned}USDT"

    def execute_tool_safely(self, tool_name: str, input_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Execute a tool with error handling and result parsing.

        Parameters
        ----------
        tool_name : str
            Name of the tool to execute
        input_data : dict
            Input data for the tool

        Returns
        -------
        dict | None
            Parsed tool result or None if failed
        """
        try:
            tool = self.get_tool(tool_name)
            result = tool.run(input_data)

            # Parse JSON result if it's a string
            if isinstance(result, str):
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    return {"raw_result": result}

            return result if isinstance(result, dict) else {"raw_result": result}

        except Exception as e:
            logger.warning("Tool execution failed for %s: %s", tool_name, e)
            return None

    def execute_agent_safely(self, agent_name: str, state: dict[str, Any]) -> dict[str, Any] | None:
        """
        Execute an agent with error handling.

        Parameters
        ----------
        agent_name : str
            Name of the agent to execute
        state : dict
            State data for the agent

        Returns
        -------
        dict | None
            Agent result or None if failed
        """

        def _run_coroutine_sync(coro):
            """Run an async coroutine from a synchronous context.

            If there is an active event loop, run the coroutine in a separate thread
            using asyncio.run() to avoid nested event loop errors. Otherwise use
            asyncio.run() directly.
            """
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # Run the coroutine in a new thread to avoid nested event loop
                def _runner():
                    return asyncio.run(coro)

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    fut = ex.submit(_runner)
                    return fut.result()
            else:
                return asyncio.run(coro)

        try:
            agent = self.get_agent(agent_name)

            # Prefer async execution if agent provides 'arun_agent'
            if hasattr(agent, "arun_agent"):
                try:
                    coro = agent.arun_agent(state, progress_tracker=None)
                    if asyncio.iscoroutine(coro):
                        return _run_coroutine_sync(coro)
                except TypeError:
                    # arun_agent may be a regular function; ignore and fall back
                    pass

            # Fall back to synchronous run_agent
            result = agent.run_agent(state, progress_tracker=None)

            # If result is a coroutine (agent implemented async analyze_symbol), run it
            if asyncio.iscoroutine(result):
                return _run_coroutine_sync(result)

            return result if isinstance(result, dict) else {"raw_result": result}

        except Exception as e:
            logger.warning("Agent execution failed for %s: %s", agent_name, e)
            return None

    def get_news_data(self, symbol: str, max_results: int = 10) -> dict[str, Any]:
        """
        Get news data for a symbol using multiple sources.

        Parameters
        ----------
        symbol : str
            Trading symbol
        max_results : int
            Maximum number of results

        Returns
        -------
        dict
            News data with headlines and metadata
        """
        headlines = []

        try:
            # Use crypto_news_search tool which combines DuckDuckGo and RSS
            news_tool = self.get_tool("crypto_news_search")
            news_json_str = news_tool.invoke({"symbol": symbol, "max_results": max_results, "include_rss": True})

            # Parse the JSON response
            news_data = json.loads(news_json_str)

            # Convert to headlines format
            if isinstance(news_data, list):
                headlines = [
                    {
                        "title": item.get("title", ""),
                        "description": item.get("snippet", item.get("description", "")),
                        "link": item.get("link", item.get("url", "")),
                        "source": item.get("source", "web"),
                        "published": item.get("date", ""),
                    }
                    for item in news_data
                ]
            else:
                logger.warning("Unexpected news data format for %s: %s", symbol, type(news_data))

        except Exception as e:
            logger.debug("News fetch failed for %s: %s", symbol, e)

        return {
            "news_count": len(headlines),
            "headlines": headlines[:max_results],
            "sources": ["RSS", "Web Search"],
        }

    def get_sentiment_data(self, symbol: str, max_results: int = 5) -> dict[str, Any]:
        """
        Get sentiment data for a symbol using multiple tools.

        Parameters
        ----------
        symbol : str
            Trading symbol
        max_results : int
            Maximum number of results

        Returns
        -------
        dict
            Sentiment data from multiple sources
        """
        sentiment_data = {}

        try:
            news_tool = self.get_tool("crypto_news_search")
            news_sentiment = news_tool.run({"symbol": symbol, "max_results": max_results})
            sentiment_data["news_sentiment"] = news_sentiment
        except Exception as e:
            logger.debug("News sentiment failed for %s: %s", symbol, e)
            sentiment_data["news_sentiment"] = {}

        try:
            web_tool = self.get_tool("crypto_web_sentiment")
            web_sentiment = web_tool.run({"symbol": symbol, "max_results": max_results})
            sentiment_data["web_sentiment"] = web_sentiment
        except Exception as e:
            logger.debug("Web sentiment failed for %s: %s", symbol, e)
            sentiment_data["web_sentiment"] = {}

        return sentiment_data

    def get_technical_data(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> dict[str, Any]:
        """
        Get technical analysis data for a symbol.

        Parameters
        ----------
        symbol : str
            Trading symbol
        timeframe : str
            Timeframe for analysis
        limit : int
            Number of historical periods

        Returns
        -------
        dict
            Technical analysis data
        """
        aster_symbol = self.to_aster_symbol(symbol)
        technical_data = {}

        try:
            # Get price data
            price_data = self.execute_tool_safely("aster_price", {"symbol": aster_symbol})
            technical_data["price_data"] = price_data
        except Exception as e:
            logger.debug("Price data failed for %s: %s", symbol, e)
            technical_data["price_data"] = None

        try:
            # Get historical data
            historical_data = self.execute_tool_safely(
                "aster_history", {"symbol": aster_symbol, "timeframe": timeframe, "limit": limit}
            )
            technical_data["historical_data"] = historical_data
        except Exception as e:
            logger.debug("Historical data failed for %s: %s", symbol, e)
            technical_data["historical_data"] = None

        try:
            # Calculate indicators if we have historical data
            if technical_data.get("historical_data"):
                indicators = self.execute_tool_safely(
                    "technical_indicators", {"symbol": symbol, "klines": technical_data["historical_data"]}
                )
                technical_data["indicators"] = indicators
        except Exception as e:
            logger.debug("Indicators calculation failed for %s: %s", symbol, e)
            technical_data["indicators"] = {}

        return technical_data

    def cleanup(self) -> None:
        """Clean up resources."""
        self._tools.clear()
        self._agents.clear()
