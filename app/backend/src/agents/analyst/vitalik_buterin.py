"""
Vitalik Buterin Agent - Ethereum Founder and Crypto Visionary.

This agent embodies the philosophy of Ethereum's creator, focusing on:
- Smart contracts and decentralized applications
- Scalability and layer 2 solutions
- Decentralized governance and DAOs
- Cryptoeconomic incentives
- Long-term sustainability
- Innovation and technical excellence
"""

from typing import Any

from app.backend.src.agents.base_agent import BaseCryptoAgent
from app.backend.src.graph.enhanced_state import CryptoAgentState
from app.backend.src.utils.llm import call_llm_with_retry
from pydantic import BaseModel


class VitalikAnalysis(BaseModel):
    """Analysis output from Vitalik Buterin Agent for FUTURES trading."""

    recommendation: str  # "LONG", "SHORT", "HOLD" (for futures positions)
    confidence: float  # 0.0 to 1.0
    reasoning: str
    technical_innovation: float  # 0.0 to 1.0
    scalability_potential: float  # 0.0 to 1.0
    smart_contract_utility: float  # 0.0 to 1.0
    governance_quality: float  # 0.0 to 1.0
    cryptoeconomic_design: float  # 0.0 to 1.0
    long_term_sustainability: float  # 0.0 to 1.0
    risk_assessment: str
    key_insights: list[str]
    # Futures-specific fields
    leverage_recommendation: float | None = None  # 1-5x for conservative tech-focused trades
    sustainability_risk: str | None = None  # "LOW", "MEDIUM", "HIGH" (for long-term holds)


class VitalikButerinAgent(BaseCryptoAgent):
    """
    Vitalik Buterin Agent - Ethereum Founder and Crypto Visionary.

    This agent analyzes cryptocurrencies through the lens of Ethereum's creator,
    focusing on technical innovation, scalability, and decentralized applications.
    """

    def __init__(
        self,
        agent_id: str = "vitalik_buterin",
        use_langchain: bool = False,
        model_name: str | None = None,
        model_provider: str | None = None,
    ):
        self.persona = """
        You are Vitalik Buterin, co-founder of Ethereum and blockchain visionary. Your philosophy centers on:

        1. TECHNICAL INNOVATION: Value projects that push the boundaries of blockchain technology
        2. SCALABILITY: Focus on solving the blockchain trilemma (security, scalability, decentralization)
        3. SMART CONTRACTS: Evaluate the power and security of programmable money
        4. GOVERNANCE: Appreciate thoughtful governance models and cryptoeconomic design
        5. SUSTAINABILITY: Consider long-term sustainability and environmental impact
        6. COMMUNITY: Value strong developer communities and ecosystem growth

        You analyze cryptocurrencies based on:
        - Technical innovation (novel consensus mechanisms, scaling solutions)
        - Smart contract capabilities (expressiveness, security, gas efficiency)
        - Scalability solutions (layer 2s, sharding, rollups)
        - Governance models (on-chain governance, community decision making)
        - Developer activity (commits, contributors, documentation)
        - Ecosystem growth (dApps, users, total value locked)

        You are thoughtful, technically rigorous, and appreciate projects
        that advance the state of blockchain technology beyond simple speculation.
        """
        super().__init__(
            agent_id,
            "Vitalik Buterin Agent",
            use_langchain=use_langchain,
            model_name=model_name,
            model_provider=model_provider,
        )

    def _get_langchain_prompt(self) -> str:
        """Get custom LangChain prompt for Vitalik Buterin agent."""
        return (
            self.persona
            + """

Your role is to analyze cryptocurrencies from an Ethereum ecosystem perspective:
1. Gather technical and market data
2. Evaluate technical innovation and scalability
3. Assess smart contract capabilities and security
4. Check governance and cryptoeconomic design
5. Provide clear trading signals

📊 PORTFOLIO AWARENESS:
Check for EXISTING position before recommending. Factor in current holdings when evaluating technical merits.

Always provide:
- Recommendation: BUY, SELL, or HOLD
- Confidence: 0-1 (your certainty level)
- Reasoning: detailed technical analysis
- Scores for innovation, scalability, smart contracts, governance, and sustainability

Focus on projects that push blockchain technology forward."""
        )

    async def _analyze_symbol_manual(
        self, symbol: str, state: CryptoAgentState, _progress_tracker=None
    ) -> dict[str, Any]:
        """
        Analyze a cryptocurrency symbol through Vitalik's lens.

        Parameters
        ----------
        symbol : str
            The cryptocurrency symbol to analyze (e.g., "ETH/USDT")
        state : CryptoAgentState
            The current agent state with market data

        Returns
        -------
        dict[str, Any]
            Analysis results including recommendation and reasoning
        """
        try:
            # Extract symbol without exchange suffix
            base_symbol = symbol.split("/")[0] if "/" in symbol else symbol

            # Get data from the state (collected by data_collection node)
            price_data = state.get("price_data", {}).get(symbol, {})
            volume_data = state.get("volume_data", {}).get(symbol, {})
            news_data = state.get("news_data", {}).get(symbol, {})

            # Get portfolio data
            portfolio = state.get("data", {}).get("portfolio", {})
            total_value = portfolio.get("total_value", 0)
            cash = portfolio.get("cash", 0)

            # Extract key metrics from collected data
            if hasattr(price_data, "price"):
                # PriceData object - access attributes directly
                current_price = price_data.price
                volume_24h = price_data.volume
                change_percent_24h = price_data.change_percent_24h
                high_24h = price_data.high_24h
                low_24h = price_data.low_24h
            else:
                # Dictionary - use get method
                current_price = price_data.get("price", 0)
                volume_24h = price_data.get("volume", 0)
                change_percent_24h = price_data.get("change_percent_24h", 0)
                high_24h = price_data.get("high_24h", 0)
                low_24h = price_data.get("low_24h", 0)

            # Get volume metrics from volume_data
            current_volume = volume_data.get("current_volume", 0)
            avg_volume = volume_data.get("avg_volume", 0)
            volume_trend = volume_data.get("volume_trend", "unknown")

            # Get news sentiment from news_data
            news_count = news_data.get("news_count", 0)
            headlines = news_data.get("headlines", [])

            # Build analysis context using collected data
            analysis_context = f"""
            Market Data for {symbol}:

            PRICE METRICS:
            - Current Price: ${current_price:,.2f}
            - 24h Change: {change_percent_24h:,.2f}%
            - 24h High: ${high_24h:,.2f}
            - 24h Low: ${low_24h:,.2f}

            VOLUME METRICS:
            - Current Volume: ${current_volume:,.2f}
            - Average Volume: ${avg_volume:,.2f}
            - Volume Trend: {volume_trend}

            NEWS METRICS:
            - News Count: {news_count}
            - Recent Headlines: {headlines[:3] if headlines else "None"}

            TECHNICAL METRICS:
            - Price Trend: {"uptrend" if change_percent_24h > 0 else "downtrend" if change_percent_24h < 0 else "sideways"}
            - Volume Activity: {"high" if current_volume > avg_volume * 1.2 else "low" if current_volume < avg_volume * 0.8 else "normal"}
            - Market Interest: {"high" if news_count > 5 else "low" if news_count < 2 else "moderate"}

            ADOPTION METRICS:
            - Developer Activity: {"high" if news_count > 3 else "low" if news_count < 1 else "moderate"}
            - Network Activity: {"high" if current_volume > avg_volume * 1.5 else "low" if current_volume < avg_volume * 0.5 else "normal"}
            - Market Sentiment: {"positive" if change_percent_24h > 0 else "negative" if change_percent_24h < 0 else "neutral"}
            """

            # Create analysis prompt
            prompt = f"""
            As Vitalik Buterin, analyze the cryptocurrency {base_symbol} (${symbol}) at current price ${current_price:,.2f}.

            {analysis_context}

            Consider the following factors:

            1. TECHNICAL INNOVATION:
            - What novel technical features does this project introduce?
            - How does it advance the state of blockchain technology?
            - Are there any breakthrough cryptographic techniques?

            2. SCALABILITY SOLUTIONS:
            - How does it handle scalability challenges?
            - Does it implement layer 2 solutions or other scaling techniques?
            - What is the transaction throughput and finality time?

            3. SMART CONTRACT CAPABILITIES:
            - What smart contract functionality does it support?
            - How secure and efficient are the contracts?
            - What developer tools and ecosystem exist?

            4. GOVERNANCE MECHANISMS:
            - How is the network governed?
            - Are there DAO structures or community voting?
            - How are protocol upgrades handled?

            5. CRYPTOECONOMIC DESIGN:
            - What is the token utility and economic model?
            - How are validators/miners incentivized?
            - Is the fee structure sustainable?

            6. DEVELOPER ECOSYSTEM:
            - What tools and documentation are available?
            - How active is the developer community?
            - What applications are built on top?

            7. LONG-TERM VISION:
            - What is the roadmap and long-term goals?
            - How does it contribute to the broader ecosystem?
            - What real-world problems does it solve?

            Portfolio Context:
            - Current portfolio value: ${total_value:,.2f}
            - Available cash: ${cash:,.2f}

            Provide your FUTURES analysis in the following JSON format:
            {{
                "recommendation": "LONG|SHORT|HOLD",
                "confidence": 0.0-1.0,
                "reasoning": "Detailed explanation: WHY LONG or SHORT based on technical fundamentals",
                "technical_innovation": 0.0-1.0,
                "scalability_potential": 0.0-1.0,
                "smart_contract_utility": 0.0-1.0,
                "governance_quality": 0.0-1.0,
                "cryptoeconomic_design": 0.0-1.0,
                "long_term_sustainability": 0.0-1.0,
                "risk_assessment": "LOW|MEDIUM|HIGH",
                "key_insights": ["insight1", "insight2", "insight3"],
                "leverage_recommendation": 1.0-5.0 (conservative, focus on quality over speculation),
                "sustainability_risk": "LOW|MEDIUM|HIGH"
            }}

            FUTURES STRATEGY (Vitalik's Technical Approach):
            - LONG: Strong technical fundamentals + growing ecosystem + scaling solutions working
            - SHORT: Technical limitations + stagnant development + better alternatives emerging
            - Leverage: Conservative 1-3x (you value sustainability over aggressive speculation)
            - Focus: ETH ecosystem projects, L2 scaling solutions, innovative consensus mechanisms

            Remember: You are the founder of Ethereum. Focus on technical innovation,
            ecosystem development, and long-term sustainability. For FUTURES trading, prefer
            LONG positions on technically superior projects with strong fundamentals.
            Be cautious with leverage (max 3-5x) as you value long-term viability over short-term gains.
            """

            # Call LLM for analysis
            analysis = call_llm_with_retry(
                prompt=prompt,
                pydantic_model=VitalikAnalysis,
                agent_name=self.agent_name,
                state=state,
            )

            return {
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "symbol": symbol,
                "signal": analysis.recommendation,
                "recommendation": analysis.recommendation,
                "confidence": analysis.confidence,
                "reasoning": analysis.reasoning,
                "technical_innovation": analysis.technical_innovation,
                "scalability_potential": analysis.scalability_potential,
                "smart_contract_utility": analysis.smart_contract_utility,
                "governance_quality": analysis.governance_quality,
                "cryptoeconomic_design": analysis.cryptoeconomic_design,
                "long_term_sustainability": analysis.long_term_sustainability,
                "risk_assessment": analysis.risk_assessment,
                "key_insights": analysis.key_insights,
                "timestamp": self.get_current_timestamp(),
            }

        except Exception as e:
            return {
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "symbol": symbol,
                "signal": "HOLD",
                "recommendation": "HOLD",
                "confidence": 0.0,
                "reasoning": f"Error in analysis: {e!s}",
                "technical_innovation": 0.0,
                "scalability_potential": 0.0,
                "smart_contract_utility": 0.0,
                "governance_quality": 0.0,
                "cryptoeconomic_design": 0.0,
                "long_term_sustainability": 0.0,
                "risk_assessment": "HIGH",
                "key_insights": ["Analysis failed"],
                "timestamp": self.get_current_timestamp(),
            }

    def get_signal_model(self) -> type[BaseModel]:
        """
        Get the Pydantic model for the agent's signal output.

        Returns
        -------
        type[BaseModel]
            Pydantic model class for the signal
        """
        return VitalikAnalysis

    def get_llm_prompt_template(self) -> str:
        """
        Get the LLM prompt template for generating analysis.

        Returns
        -------
        str
            Prompt template string
        """
        return """
        As Vitalik Buterin, analyze the cryptocurrency {symbol} based on the following data:

        {analysis_data}

        Focus on:
        1. Technical innovation and scalability
        2. Smart contract capabilities
        3. Governance mechanisms
        4. Cryptoeconomic design
        5. Developer ecosystem
        6. Long-term sustainability

        Provide your analysis in the following JSON format:
        {{
            "recommendation": "BUY|SELL|HOLD",
            "confidence": 0.0-1.0,
            "reasoning": "Detailed explanation of your analysis",
            "technical_innovation": 0.0-1.0,
            "scalability_potential": 0.0-1.0,
            "smart_contract_utility": 0.0-1.0,
            "governance_quality": 0.0-1.0,
            "cryptoeconomic_design": 0.0-1.0,
            "long_term_sustainability": 0.0-1.0,
            "risk_assessment": "LOW|MEDIUM|HIGH",
            "key_insights": ["insight1", "insight2", "insight3"]
        }}
        """
