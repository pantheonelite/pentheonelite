"""LangChain agent creation helpers for crypto trading agents.

This module provides utilities to create LangChain ReAct agents with crypto tools,
enabling LLM-driven tool selection and iterative reasoning for trading decisions.
"""

from typing import Any

from app.backend.config.llm import get_llm_settings
from app.backend.src.tools.crypto import (
    aster_get_history,
    aster_get_multi_price,
    aster_get_price,
    crypto_sentiment_analysis,
    price_trend_analysis,
    technical_indicators_analysis,
    trading_strategy_analysis,
    volume_analysis,
)
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.chat_models import ChatLiteLLM
from langchain_core.prompts import PromptTemplate


def get_crypto_tools() -> list:
    """
    Get the list of crypto trading tools.

    Returns
    -------
    list
        List of LangChain tools for crypto analysis
    """
    return [
        aster_get_price,
        aster_get_history,
        aster_get_multi_price,
        technical_indicators_analysis,
        price_trend_analysis,
        volume_analysis,
        crypto_sentiment_analysis,
        trading_strategy_analysis,
    ]


def create_crypto_react_agent(
    system_prompt: str,
    model_name: str | None = None,
    temperature: float = 0.1,
    max_iterations: int = 10,
    verbose: bool = False,
) -> tuple[AgentExecutor, list]:
    """
    Create a LangChain ReAct agent for crypto trading analysis.

    Parameters
    ----------
    system_prompt : str
        System prompt describing the agent's role and expertise
    model_name : str | None, optional
        LLM model name, if None uses LiteLLM settings, by default None
    temperature : float, optional
        LLM temperature (0-1), by default 0.1
    max_iterations : int, optional
        Max reasoning iterations, by default 10
    verbose : bool, optional
        Enable verbose logging, by default False

    Returns
    -------
    tuple[AgentExecutor, list]
        Tuple of (agent_executor, tools_list)

    Examples
    --------
    >>> executor, tools = create_crypto_react_agent(
    ...     system_prompt="You are a technical analyst...",
    ...     model_name="gpt-4o-mini"
    ... )
    >>> result = executor.invoke({"input": "Analyze BTCUSDT"})
    """
    # Get LLM settings
    llm_settings = get_llm_settings()

    # Use model_name if provided, otherwise use LiteLLM settings
    model = model_name or llm_settings.litellm_model

    # Initialize LiteLLM
    llm = ChatLiteLLM(
        model=model,
        temperature=temperature,
        api_key=llm_settings.litellm_api_key,
        api_base=llm_settings.litellm_base_url,
        timeout=llm_settings.litellm_timeout,
        max_tokens=llm_settings.litellm_max_tokens,
    )

    # Get crypto tools
    tools = get_crypto_tools()

    # Create ReAct prompt template
    template = f"""{system_prompt}

You have access to the following tools:

{{tools}}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{{tool_names}}]
Action Input: the input to the action (must be valid JSON)
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {{input}}
Thought: {{agent_scratchpad}}"""

    prompt = PromptTemplate.from_template(template)

    # Create ReAct agent
    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

    # Create agent executor
    executor = AgentExecutor(
        agent=agent, tools=tools, verbose=verbose, max_iterations=max_iterations, handle_parsing_errors=True
    )

    return executor, tools


def create_persona_agent(
    persona_name: str,
    expertise: str,
    personality_traits: str,
    analysis_focus: str,
    model_name: str | None = None,
    temperature: float = 0.3,
    max_iterations: int = 10,
    verbose: bool = False,
) -> tuple[AgentExecutor, list]:
    """
    Create a persona-based LangChain agent for crypto trading.

    Parameters
    ----------
    persona_name : str
        Name of the persona (e.g., "Satoshi Nakamoto")
    expertise : str
        Domain of expertise (e.g., "Bitcoin fundamentals")
    personality_traits : str
        Key personality characteristics
    analysis_focus : str
        What the persona focuses on in analysis
    model_name : str | None, optional
        LLM model name, if None uses LiteLLM settings, by default None
    temperature : float, optional
        LLM temperature (0-1), by default 0.3
    max_iterations : int, optional
        Max reasoning iterations, by default 10
    verbose : bool, optional
        Enable verbose logging, by default False

    Returns
    -------
    tuple[AgentExecutor, list]
        Tuple of (agent_executor, tools_list)

    Examples
    --------
    >>> executor, tools = create_persona_agent(
    ...     persona_name="Vitalik Buterin",
    ...     expertise="Ethereum and smart contracts",
    ...     personality_traits="Thoughtful, technical, long-term focused",
    ...     analysis_focus="Technology fundamentals and ecosystem"
    ... )
    """
    system_prompt = f"""You are {persona_name}, a cryptocurrency expert.

Expertise: {expertise}
Personality: {personality_traits}
Analysis Focus: {analysis_focus}

Your role is to provide trading analysis from your unique perspective, using available tools
to gather data and form opinions that align with your expertise and personality.

Guidelines:
- Stay true to {persona_name}'s known views and expertise
- Use technical and market data tools to support your analysis
- Provide clear trading signals: buy, sell, or hold
- Explain your reasoning based on your expertise
- Be confident but acknowledge uncertainty when appropriate"""

    return create_crypto_react_agent(
        system_prompt=system_prompt,
        model_name=model_name,
        temperature=temperature,
        max_iterations=max_iterations,
        verbose=verbose,
    )


def invoke_agent_for_symbol(executor: AgentExecutor, symbol: str) -> dict[str, Any]:
    """
    Invoke a LangChain agent to analyze a specific cryptocurrency symbol.

    Parameters
    ----------
    executor : AgentExecutor
        LangChain AgentExecutor instance
    symbol : str
        Cryptocurrency symbol (e.g., "BTCUSDT")
    agent_name : str, optional
        Agent name for logging, by default "Crypto Agent"

    Returns
    -------
    dict[str, Any]
        Analysis result containing output, intermediate steps, etc.

    Examples
    --------
    >>> executor, _ = create_crypto_react_agent("You are a trader...")
    >>> result = invoke_agent_for_symbol(executor, "BTCUSDT", "Technical Analyst")
    """
    query = f"""Analyze {symbol} and provide a trading recommendation.

Your analysis should:
1. Gather current price and historical data
2. Analyze technical indicators
3. Check volume patterns
4. Consider market sentiment
5. Provide a clear signal: buy, sell, or hold
6. Explain your reasoning with confidence level (0-1)

Return your final answer as a JSON object with:
- signal: "buy", "sell", or "hold"
- confidence: number between 0 and 1
- reasoning: detailed explanation
- price_target: optional target price
- stop_loss: optional stop loss price"""

    try:
        return executor.invoke({"input": query})
    except Exception as e:
        return {
            "output": f"Error: {e!s}",
            "signal": "hold",
            "confidence": 0.0,
            "reasoning": f"Agent execution failed: {e!s}",
        }


async def ainvoke_agent_for_symbol(executor: AgentExecutor, symbol: str) -> dict[str, Any]:
    """
    Asynchronously invoke a LangChain agent to analyze a cryptocurrency symbol.

    Parameters
    ----------
    executor : AgentExecutor
        LangChain AgentExecutor instance
    symbol : str
        Cryptocurrency symbol (e.g., "BTCUSDT")
    agent_name : str, optional
        Agent name for logging, by default "Crypto Agent"

    Returns
    -------
    dict[str, Any]
        Analysis result containing output, intermediate steps, etc.

    Examples
    --------
    >>> executor, _ = create_crypto_react_agent("You are a trader...")
    >>> result = await ainvoke_agent_for_symbol(executor, "BTCUSDT")
    """
    query = f"""Analyze {symbol} and provide a trading recommendation.

Your analysis should:
1. Gather current price and historical data
2. Analyze technical indicators
3. Check volume patterns
4. Consider market sentiment
5. Provide a clear signal: buy, sell, or hold
6. Explain your reasoning with confidence level (0-1)

Return your final answer as a JSON object with:
- signal: "buy", "sell", or "hold"
- confidence: number between 0 and 1
- reasoning: detailed explanation
- price_target: optional target price
- stop_loss: optional stop loss price"""

    try:
        return await executor.ainvoke({"input": query})
    except Exception as e:
        return {
            "output": f"Error: {e!s}",
            "signal": "hold",
            "confidence": 0.0,
            "reasoning": f"Agent execution failed: {e!s}",
        }
