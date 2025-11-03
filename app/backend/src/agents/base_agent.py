"""Base agent class for crypto trading agents."""

import asyncio
import json
import re
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any, cast

import structlog
from app.backend.src.graph.enhanced_state import CryptoAgentState
from app.backend.src.graph.state import show_agent_reasoning
from app.backend.src.utils.llm import call_llm_with_retry
from app.backend.src.utils.progress import get_progress
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class BaseCryptoAgent(ABC):
    """Base class for all crypto trading agents.

    Supports both manual workflow and LangChain ReAct agent modes.
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        use_langchain: bool = False,
        model_name: str | None = None,
        model_provider: str | None = None,
    ):
        """
        Initialize the base crypto agent.

        Parameters
        ----------
        agent_id : str
            Unique identifier for the agent
        agent_name : str
            Human-readable name for the agent
        use_langchain : bool, optional
            If True, use LangChain ReAct agent for analysis.
            If False, use manual workflow. Default is False.
        model_name : str | None, optional
            Model name to use for LLM calls (e.g., "gpt-4o-mini", "claude-3-sonnet").
            If None, uses state or default model.
        model_provider : str | None, optional
            Model provider to use (e.g., "OPENAI", "ANTHROPIC", "OPENROUTER").
            If None, uses state or default provider.
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.use_langchain = use_langchain
        self.model_name = model_name
        self.model_provider = model_provider
        self.langchain_executor = None
        self.langchain_tools = None

        # Initialize LangChain agent if enabled
        if use_langchain:
            self._init_langchain_agent()

    def _init_langchain_agent(self):
        """
        Initialize LangChain ReAct agent for this agent.

        Subclasses can override this to use persona-specific agents.
        """
        # Import here to avoid circular dependency and only when needed
        from app.backend.src.agents.langchain_helpers import create_crypto_react_agent  # noqa: PLC0415

        system_prompt = self._get_langchain_prompt()
        self.langchain_executor, self.langchain_tools = create_crypto_react_agent(
            system_prompt=system_prompt, model_name="gpt-4o-mini", temperature=0.1, max_iterations=10
        )
        logger.info("Initialized LangChain agent for %s", self.agent_id)

    def _get_langchain_prompt(self) -> str:
        """
        Get system prompt for LangChain ReAct agent.

        Subclasses should override this to provide agent-specific prompts.

        Returns
        -------
        str
            System prompt for the LangChain agent
        """
        return f"""You are {self.agent_name}, a cryptocurrency trading analyst.

Provide clear, data-driven trading recommendations using the available tools.
Always gather relevant data before making decisions.

Your analysis should include:
- Current price and trends
- Technical indicators
- Volume patterns
- Market sentiment (when relevant)
- Clear trading signal: buy, sell, or hold
- Confidence level (0-1)
- Detailed reasoning"""

    async def analyze_symbol(self, symbol: str, state: CryptoAgentState, progress_tracker=None) -> dict[str, Any]:
        """
        Analyze a single crypto symbol.

        Routes to either LangChain mode or manual mode based on use_langchain flag.

        Parameters
        ----------
        symbol : str
            The crypto symbol to analyze (e.g., "BTC/USDT")
        state : CryptoAgentState
            The current agent state
        progress_tracker : optional
            Progress tracker instance for detailed updates

        Returns
        -------
        dict[str, Any]
            Analysis results for the symbol
        """
        if self.use_langchain:
            return await self._analyze_symbol_langchain(symbol, state, progress_tracker)
        return await self._analyze_symbol_manual(symbol, state, progress_tracker)

    async def _analyze_symbol_langchain(
        self, symbol: str, _state: CryptoAgentState, progress_tracker=None
    ) -> dict[str, Any]:
        """
        Analyze symbol using LangChain ReAct agent.

        Parameters
        ----------
        symbol : str
            The crypto symbol to analyze
        _state : CryptoAgentState
            The current agent state (unused in LangChain mode)
        progress_tracker : optional
            Progress tracker instance

        Returns
        -------
        dict[str, Any]
            Analysis result containing signal, confidence, reasoning
        """
        if self.langchain_executor is None:
            raise RuntimeError("LangChain agent not initialized. Set use_langchain=True in constructor.")

        if progress_tracker:
            progress_tracker.update_status(self.agent_id, symbol, "Analyzing with LangChain ReAct agent...")
        else:
            get_progress().update_status(self.agent_id, symbol, "Analyzing with LangChain ReAct agent...")

        try:
            # Import here to avoid circular dependency
            from app.backend.src.agents.langchain_helpers import ainvoke_agent_for_symbol  # noqa: PLC0415

            result = await ainvoke_agent_for_symbol(self.langchain_executor, symbol)

            # Parse LangChain result to extract signal, confidence, reasoning
            return self._parse_langchain_result(result)

        except Exception as e:
            logger.exception("Error in LangChain agent for %s", symbol)
            return {
                "signal": "hold",
                "confidence": 0.0,
                "reasoning": f"LangChain agent error: {e!s}",
                "agent_id": self.agent_id,
                "timestamp": self.get_current_timestamp(),
            }

    def _parse_langchain_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """
        Parse LangChain agent result into standard format.

        Parameters
        ----------
        result : dict[str, Any]
            Raw result from LangChain agent

        Returns
        -------
        dict[str, Any]
            Parsed result with signal, confidence, reasoning
        """
        output = result.get("output", "")

        # Try to extract structured data from output
        # LLMs often return JSON in the output
        signal = "hold"
        confidence = 0.5
        reasoning = output

        # Simple parsing - look for keywords
        output_lower = output.lower()
        if "buy" in output_lower and "sell" not in output_lower:
            signal = "buy"
        elif "sell" in output_lower and "buy" not in output_lower:
            signal = "sell"
        else:
            signal = "hold"

        # Try to extract confidence (look for numbers between 0-1 or 0-100)
        confidence_match = re.search(r"confidence[:\s]+([0-9.]+)", output_lower)
        if confidence_match:
            conf_val = float(confidence_match.group(1))
            confidence = conf_val if conf_val <= 1.0 else conf_val / 100.0
        else:
            # Default based on signal strength
            confidence = 0.7 if signal != "hold" else 0.5

        return {
            "signal": signal,
            "confidence": confidence,
            "reasoning": reasoning[:500] if len(reasoning) > 500 else reasoning,  # Truncate if too long
            "agent_id": self.agent_id,
            "timestamp": self.get_current_timestamp(),
            "mode": "langchain",
        }

    @abstractmethod
    async def _analyze_symbol_manual(
        self, symbol: str, state: CryptoAgentState, progress_tracker=None
    ) -> dict[str, Any]:
        """
        Analyze symbol using manual workflow (existing implementation).

        Subclasses must implement this with their existing logic.

        Parameters
        ----------
        symbol : str
            The crypto symbol to analyze
        state : CryptoAgentState
            The current agent state
        progress_tracker : optional
            Progress tracker instance

        Returns
        -------
        dict[str, Any]
            Analysis result containing signal, confidence, reasoning
        """
        raise NotImplementedError("Subclasses must implement manual analysis")

    @abstractmethod
    def get_signal_model(self) -> type[BaseModel]:
        """
        Get the Pydantic model for the agent's signal output.

        Returns
        -------
        type[BaseModel]
            Pydantic model class for the signal
        """
        raise NotImplementedError

    @abstractmethod
    def get_llm_prompt_template(self) -> ChatPromptTemplate:
        """
        Get the LLM prompt template for generating analysis.

        Returns
        -------
        ChatPromptTemplate
            LangChain prompt template
        """
        raise NotImplementedError

    def run_agent(self, state: CryptoAgentState, progress_tracker=None) -> dict[str, Any]:
        """
        Run the agent synchronously.

        Parameters
        ----------
        state : CryptoAgentState
            The current agent state
        progress_tracker : optional
            Progress tracker instance

        Returns
        -------
        dict[str, Any]
            Updated state with agent results
        """
        symbols = state.get("symbols", [])

        # Initialize results storage
        results_key = self._get_results_key()
        # Cast to regular dict for dynamic key access
        state_dict = cast("dict[str, Any]", state)
        if results_key not in state_dict:
            state_dict[results_key] = {}

        agent_results = {}

        for i, symbol in enumerate(symbols, 1):
            try:
                # Use provided progress_tracker or get_progress()
                if progress_tracker:
                    progress_tracker.update_status(
                        self.agent_id, symbol, f"Starting {self.agent_name} analysis ({i}/{len(symbols)})..."
                    )
                else:
                    get_progress().update_status(
                        self.agent_id, symbol, f"Starting {self.agent_name} analysis ({i}/{len(symbols)})..."
                    )

                # Log agent progress
                logger.info("Processing %s with %s (%d/%d)", symbol, self.agent_name, i, len(symbols))

                # Analyze the symbol (should be synchronous in run_agent)
                analysis_result = asyncio.run(self.analyze_symbol(symbol, state, progress_tracker))
                agent_results[symbol] = analysis_result

                # Log completion
                logger.info("Completed %s analysis for %s", self.agent_name, symbol)

                if progress_tracker:
                    progress_tracker.update_status(
                        self.agent_id,
                        symbol,
                        "Done",
                        analysis=analysis_result.get("reasoning", ""),
                    )
                else:
                    get_progress().update_status(
                        self.agent_id,
                        symbol,
                        "Done",
                        analysis=analysis_result.get("reasoning", ""),
                    )

            except Exception as e:
                error_msg = f"Error analyzing {symbol}: {e!s}"
                if progress_tracker:
                    progress_tracker.update_status(self.agent_id, symbol, "Error", analysis=error_msg)
                else:
                    get_progress().update_status(self.agent_id, symbol, "Error", analysis=error_msg)
                agent_results[symbol] = {
                    "signal": "hold",
                    "confidence": 0.0,
                    "reasoning": error_msg,
                    "error": str(e),
                }

        # Store results in state (convert Pydantic models to dicts for JSON serialization)
        serializable_results = {}
        for symbol, result in agent_results.items():
            if isinstance(result, dict):
                serializable_results[symbol] = result
            else:
                # Convert Pydantic model to dict
                serializable_results[symbol] = result.model_dump() if hasattr(result, "model_dump") else result

        state_dict[results_key][self.agent_id] = serializable_results

        # Show reasoning if enabled
        if state.get("metadata", {}).get("show_reasoning", False):
            show_agent_reasoning(serializable_results, self.agent_name)

        # Create message for the workflow
        message = HumanMessage(content=json.dumps(serializable_results, default=str), name=self.agent_id)

        if progress_tracker:
            progress_tracker.update_status(self.agent_id, None, "Done")
        else:
            get_progress().update_status(self.agent_id, None, "Done")

        return {"messages": [message], results_key: {self.agent_id: serializable_results}}

    async def arun_agent(self, state: CryptoAgentState, progress_tracker=None) -> dict[str, Any]:
        """
        Run the agent asynchronously.

        Parameters
        ----------
        state : CryptoAgentState
            The current agent state
        progress_tracker : optional
            Progress tracker instance

        Returns
        -------
        dict[str, Any]
            Updated state with agent results
        """
        symbols = state.get("symbols", [])

        # Initialize results storage
        results_key = self._get_results_key()
        # Cast to regular dict for dynamic key access
        state_dict = cast("dict[str, Any]", state)
        if results_key not in state_dict:
            state_dict[results_key] = {}

        # Run all symbol analyses in parallel using asyncio.gather
        logger.info("Running %s analysis on %d symbols in parallel", self.agent_name, len(symbols))

        tasks = [
            self._analyze_symbol_with_tracking(symbol, i, len(symbols), state, progress_tracker)
            for i, symbol in enumerate(symbols, 1)
        ]

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        agent_results = {}
        for symbol, result in zip(symbols, results_list, strict=True):
            if isinstance(result, Exception):
                error_msg = f"Error analyzing {symbol}: {result!s}"
                logger.error(error_msg)
                if progress_tracker:
                    progress_tracker.update_status(self.agent_id, symbol, "Error", analysis=error_msg)
                else:
                    get_progress().update_status(self.agent_id, symbol, "Error", analysis=error_msg)
                agent_results[symbol] = {
                    "signal": "hold",
                    "confidence": 0.0,
                    "reasoning": error_msg,
                    "error": str(result),
                }
            else:
                agent_results[symbol] = result

        # Store results in state (convert Pydantic models to dicts for JSON serialization)
        serializable_results = {}
        for symbol, result in agent_results.items():
            if isinstance(result, dict):
                serializable_results[symbol] = result
            else:
                # Convert Pydantic model to dict
                serializable_results[symbol] = result.model_dump() if hasattr(result, "model_dump") else result

        state_dict[results_key][self.agent_id] = serializable_results

        # Show reasoning if enabled
        if state.get("metadata", {}).get("show_reasoning", False):
            show_agent_reasoning(serializable_results, self.agent_name)

        # Create message for the workflow
        message = HumanMessage(content=json.dumps(serializable_results, default=str), name=self.agent_id)

        if progress_tracker:
            progress_tracker.update_status(self.agent_id, None, "Done")
        else:
            get_progress().update_status(self.agent_id, None, "Done")

        logger.info("Completed %s analysis on %d symbols", self.agent_name, len(symbols))

        return {"messages": [message], results_key: {self.agent_id: serializable_results}}

    async def _analyze_symbol_with_tracking(
        self, symbol: str, index: int, total: int, state: CryptoAgentState, progress_tracker=None
    ) -> dict[str, Any]:
        """
        Analyze a single symbol with progress tracking.

        Parameters
        ----------
        symbol : str
            The crypto symbol to analyze
        index : int
            Current symbol index (1-based)
        total : int
            Total number of symbols
        state : CryptoAgentState
            The current agent state
        progress_tracker : optional
            Progress tracker instance

        Returns
        -------
        dict[str, Any]
            Analysis result for the symbol
        """
        try:
            # Update progress - starting analysis
            if progress_tracker:
                progress_tracker.update_status(
                    self.agent_id, symbol, f"Starting {self.agent_name} analysis ({index}/{total})..."
                )
            else:
                get_progress().update_status(
                    self.agent_id, symbol, f"Starting {self.agent_name} analysis ({index}/{total})..."
                )

            # Analyze the symbol
            analysis_result = await self.analyze_symbol(symbol, state, progress_tracker)

        except Exception:
            # Let the exception propagate to be handled by asyncio.gather
            logger.exception("Error analyzing %s with %s", symbol, self.agent_name)
            raise
        else:
            # Update progress - completed
            if progress_tracker:
                progress_tracker.update_status(
                    self.agent_id,
                    symbol,
                    "Done",
                    analysis=analysis_result.get("reasoning", ""),
                )
            else:
                get_progress().update_status(
                    self.agent_id,
                    symbol,
                    "Done",
                    analysis=analysis_result.get("reasoning", ""),
                )

            return analysis_result

    def _get_results_key(self) -> str:
        """
        Get the key for storing results in the state data.

        Returns
        -------
        str
            Key for storing results
        """
        if "analyst" in self.agent_id:
            return "analyst_signals"
        if "risk" in self.agent_id:
            return "risk_signals"
        if "portfolio" in self.agent_id:
            return "portfolio_signals"
        return "agent_signals"

    def generate_llm_analysis(self, symbol: str, analysis_data: dict[str, Any], state: CryptoAgentState) -> BaseModel:
        """
        Generate analysis using LLM.

        Parameters
        ----------
        symbol : str
            The crypto symbol being analyzed
        analysis_data : dict[str, Any]
            Raw analysis data
        state : CryptoAgentState
            The current agent state

        Returns
        -------
        BaseModel
            Generated analysis result
        """
        template = self.get_llm_prompt_template()
        prompt = template.invoke({"analysis_data": json.dumps(analysis_data, indent=2), "symbol": symbol})

        def default_signal():
            signal_model = self.get_signal_model()
            return signal_model(
                signal="hold",
                confidence=50.0,
                reasoning="Analysis incomplete; defaulting to hold",
            )

        # Override state model config with agent's model parameters if provided
        if self.model_name or self.model_provider:
            # Create a modified state with agent's model config at top level
            # CryptoAgentState has model_name and model_provider at top level, not in metadata
            modified_state = dict(state) if state else {}
            if self.model_name:
                modified_state["model_name"] = self.model_name
            if self.model_provider:
                modified_state["model_provider"] = self.model_provider
            state = modified_state

        try:
            result = call_llm_with_retry(
                prompt=prompt,
                pydantic_model=self.get_signal_model(),
                agent_name=self.agent_id,
                state=state,
            )
        except Exception:
            logger.exception("Error in agent execution")
            raise
        return result

    def safe_get_data(self, data: dict[str, Any], key: str, default: Any = None) -> Any:
        """
        Safely get data from a dictionary with a default value.

        Parameters
        ----------
        data : dict[str, Any]
            Dictionary to get data from
        key : str
            Key to look for
        default : Any
            Default value if key not found

        Returns
        -------
        Any
            Value from dictionary or default
        """
        return data.get(key, default)

    def calculate_confidence(self, scores: list[float], weights: list[float] | None = None) -> float:
        """
        Calculate weighted confidence from multiple scores.

        Parameters
        ----------
        scores : list[float]
            List of confidence scores
        weights : list[float] | None
            Optional weights for each score

        Returns
        -------
        float
            Weighted confidence score
        """
        if not scores:
            return 50.0

        if weights is None:
            weights = [1.0] * len(scores)

        if len(scores) != len(weights):
            weights = [1.0] * len(scores)

        weighted_sum = sum(score * weight for score, weight in zip(scores, weights, strict=True))
        total_weight = sum(weights)

        return max(0.0, min(100.0, weighted_sum / total_weight))

    def format_reasoning(self, reasoning_parts: list[str]) -> str:
        """
        Format reasoning from multiple parts.

        Parameters
        ----------
        reasoning_parts : list[str]
            List of reasoning components

        Returns
        -------
        str
            Formatted reasoning string
        """
        valid_parts = [part for part in reasoning_parts if part and part.strip()]
        if not valid_parts:
            return "No specific reasoning available."

        return "; ".join(valid_parts)

    def get_agent_info(self) -> dict[str, str]:
        """
        Get agent information.

        Returns
        -------
        dict[str, str]
            Agent information dictionary
        """
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_type": self.__class__.__name__,
        }

    def get_current_timestamp(self) -> str:
        """
        Get the current timestamp in ISO format.

        Returns
        -------
        str
            Current timestamp in ISO 8601 format
        """
        return datetime.now(UTC).isoformat()
