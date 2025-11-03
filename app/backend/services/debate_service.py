"""Debate service - handles agent debates and consensus determination."""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

import structlog
from app.backend.db.repositories.council_repository import CouncilRepository
from app.backend.services.portfolio_context_service import PortfolioContextService
from app.backend.src.main import run_crypto_hedge_fund
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class DebateService:
    """
    Service for executing agent debates and determining consensus.

    Handles:
    - Agent debate execution using run_crypto_hedge_fund
    - Signal parsing from workflow results
    - Consensus determination from agent votes
    - Database storage of debate messages and consensus
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the debate service.

        Parameters
        ----------
        session : AsyncSession
            Database session for repository operations
        """
        self.session = session
        self.repo = CouncilRepository(session)

    async def aexecute_debate(
        self,
        council,
        symbols: list[str],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """
        Execute agent debate using the standard workflow.

        For system councils: uses run_crypto_hedge_fund with agent keys from council.agents JSONB.
        For non-system councils: uses GraphService with custom graph structure (future implementation).

        Parameters
        ----------
        council : Council
            Council object containing is_system flag and agents JSONB field
        symbols : list[str]
            List of trading symbols to analyze
        start_date : str | None
            Start date for analysis (YYYY-MM-DD). If None, defaults to 30 days ago.
        end_date : str | None
            End date for analysis (YYYY-MM-DD). If None, defaults to today.

        Returns
        -------
        dict
            Debate results with keys:
            - success: bool
            - signals: dict[agent_id, signal_dict] (if successful)
            - error: str (if failed)
        """
        try:
            # For system councils, use the standard workflow
            if not council.is_system:
                # Non-system councils: use GraphService with custom graph (future implementation)
                logger.warning(
                    "Non-system councils not yet supported",
                    council_id=council.id,
                )
                return {"success": False, "error": "Non-system councils not yet implemented"}

            # Extract agent keys from JSONB
            agents_config = council.agents.get("agents", [])
            agent_keys = [agent_cfg["agent_key"] for agent_cfg in agents_config]

            logger.info(
                "Running standard workflow for system council",
                council_id=council.id,
                agent_keys=agent_keys,
            )

            if not agent_keys:
                return {
                    "success": False,
                    "error": "No agent keys found in system council configuration",
                }

            # Fetch real portfolio context for standard workflow
            portfolio_service = PortfolioContextService(self.session)
            portfolio_context = await portfolio_service.aget_portfolio_context(
                council=council,
                symbols=symbols,
            )

            # Convert to legacy format for standard workflow compatibility
            portfolio = {
                "cash": portfolio_context.get("available_balance", float(council.initial_capital)),
                "positions": {},
                "realized_gains": dict.fromkeys(symbols, 0.0),
                "total_value": portfolio_context.get("total_value", float(council.initial_capital)),
                "unrealized_pnl": portfolio_context.get("unrealized_pnl", 0.0),
            }

            # Map normalized positions to legacy format for each symbol
            for symbol in symbols:
                pos = portfolio_context.get("positions", {}).get(symbol, {})
                if pos:
                    side = pos.get("side", "LONG")
                    amount = pos.get("position_amt", 0.0)
                    entry = pos.get("entry_price", 0.0)

                    # Legacy format expects separate long/short amounts
                    portfolio["positions"][symbol] = {
                        "long": amount if side == "LONG" else 0.0,
                        "short": amount if side == "SHORT" else 0.0,
                        "long_cost_basis": entry if side == "LONG" else 0.0,
                        "short_cost_basis": entry if side == "SHORT" else 0.0,
                        "current_price": pos.get("current_price", entry),
                        "unrealized_pnl": pos.get("unrealized_pnl", 0.0),
                        "leverage": pos.get("leverage", 1),
                    }
                else:
                    # No position for this symbol
                    portfolio["positions"][symbol] = {
                        "long": 0.0,
                        "short": 0.0,
                        "long_cost_basis": 0.0,
                        "short_cost_basis": 0.0,
                    }

            # Get date range (default to last 30 days)
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

            # Run standard workflow in executor to avoid blocking
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: run_crypto_hedge_fund(
                    symbols=symbols,
                    start_date=start_date,
                    end_date=end_date,
                    portfolio=portfolio,
                    show_reasoning=True,
                    model_name="deepseek/deepseek-chat-v3.1",
                    model_provider="openrouter",
                ),
            )

            # Parse signals from standard workflow output (all agent types)
            # Structure: signals[symbol][agent_id] = {signal data}
            signals = self._parse_standard_workflow_signals(result)

            # Store debate messages organized by symbol, then by agent
            for symbol, agent_signals in signals.items():
                for agent_id, signal in agent_signals.items():
                    # Get display name from signal
                    agent_display_name = signal.get("agent_display_name", agent_id.replace("_", " ").title())

                    await self.repo.create_debate_message(
                        council_id=council.id,
                        agent_name=agent_display_name,
                        message=signal.get("reasoning", "Analysis performed"),
                        message_type=signal.get("message_type", "analysis"),
                        sentiment=signal.get("sentiment", "neutral"),
                        market_symbol=symbol,
                        confidence=Decimal(str(signal.get("confidence", 0.5))),
                        debate_round=1,
                    )

            return {"success": True, "signals": signals}  # noqa: TRY300

        except Exception as e:
            logger.exception("Error executing agent debate", error=str(e))
            return {"success": False, "error": str(e)}

    def _parse_standard_workflow_signals(  # noqa: C901, PLR0912
        self, workflow_result: dict
    ) -> dict[str, dict[str, dict]]:
        """
        Parse agent signals from standard workflow result.

        Extracts signals from all agent types and organizes by symbol first, then agent.
        This structure allows one agent to analyze multiple symbols efficiently.

        Extracts from:
        - analyst_signals: Technical analysis agents
        - sentiment_signals: Sentiment analysis agents
        - persona_signals: Persona agents (CZ, Vitalik, Saylor, Satoshi, Elon)
        - risk_assessments: Risk management agents

        Parameters
        ----------
        workflow_result : dict
            Result from run_crypto_hedge_fund with keys:
            - decisions: dict with final portfolio decisions
            - analyst_signals: dict[agent_id, dict[symbol, analysis]]
            - sentiment_signals: dict[symbol, analysis]
            - persona_signals: dict[agent_id, dict[symbol, analysis]]
            - risk_assessments: dict[symbol, analysis]

        Returns
        -------
        dict[str, dict[str, dict]]
            Signals organized as: signals[symbol][agent_id] = {signal_data}
            Example: signals["BTCUSDT"]["vitalik_buterin"] = {...}
        """
        # Initialize signals dict organized by symbol
        signals = {}

        # Agent display name mapping for personas (matches crypto_council_mock_data.py)
        agent_display_names = {
            "satoshi_nakamoto": "Satoshi Nakamoto",
            "vitalik_buterin": "Vitalik Buterin",
            "michael_saylor": "Michael Saylor",
            "cz_binance": "CZ (Changpeng Zhao)",
            "elon_musk": "Elon Musk",
            "crypto_technical": "Technical Analyst",
            "crypto_sentiment": "Sentiment Analyst",
            "crypto_risk_manager": "Risk Manager",
        }

        # 1. Extract technical analyst signals (from analyst_signals)
        analyst_signals = workflow_result.get("analyst_signals", {})
        for agent_id, symbol_analyses in analyst_signals.items():
            if not symbol_analyses:
                continue

            # Process each symbol this agent analyzed
            for symbol, analysis in symbol_analyses.items():
                if symbol not in signals:
                    signals[symbol] = {}

                signal = self._extract_signal_from_analysis(
                    agent_id, analysis, symbol, agent_display_names.get(agent_id)
                )
                signal["message_type"] = "technical_analysis"
                signals[symbol][agent_id] = signal

        # 2. Extract sentiment signals (flat dict by symbol)
        sentiment_signals = workflow_result.get("sentiment_signals", {}).get("crypto_sentiment", {})
        for symbol, analysis in sentiment_signals.items():
            if symbol not in signals:
                signals[symbol] = {}

            agent_id = "crypto_sentiment"
            signal = self._extract_signal_from_analysis(agent_id, analysis, symbol, agent_display_names.get(agent_id))
            signal["message_type"] = "sentiment_analysis"
            signals[symbol][agent_id] = signal

        # 3. Extract persona agent signals
        # Structure: persona_signals[agent_id][symbol] = analysis_data
        persona_signals = workflow_result.get("persona_signals", {})
        for agent_id, symbol_analyses in persona_signals.items():
            if not symbol_analyses:
                continue

            # Process each symbol this persona analyzed
            for symbol, analysis in symbol_analyses.items():
                if symbol not in signals:
                    signals[symbol] = {}

                signal = self._extract_signal_from_analysis(
                    agent_id, analysis, symbol, agent_display_names.get(agent_id)
                )
                signal["message_type"] = "persona_analysis"
                signals[symbol][agent_id] = signal

        # 4. Extract risk assessment signals (flat dict by symbol)
        risk_assessments = workflow_result.get("risk_assessments", {})
        for symbol, analysis in risk_assessments.items():
            if symbol not in signals:
                signals[symbol] = {}

            agent_id = "crypto_risk_manager"
            signal = self._extract_signal_from_analysis(agent_id, analysis, symbol, agent_display_names.get(agent_id))
            signal["message_type"] = "risk_analysis"
            signals[symbol][agent_id] = signal

        # Count signals by type for logging
        total_signals = sum(len(agent_signals) for agent_signals in signals.values())
        agent_type_counts = {"technical": 0, "sentiment": 0, "persona": 0, "risk": 0}

        for symbol_signals in signals.values():
            for signal in symbol_signals.values():
                msg_type = signal.get("message_type", "")
                if "technical" in msg_type:
                    agent_type_counts["technical"] += 1
                elif "sentiment" in msg_type:
                    agent_type_counts["sentiment"] += 1
                elif "persona" in msg_type:
                    agent_type_counts["persona"] += 1
                elif "risk" in msg_type:
                    agent_type_counts["risk"] += 1

        logger.info(
            "Parsed signals from workflow",
            total_signals=total_signals,
            symbols=list(signals.keys()),
            agent_types=agent_type_counts,
        )

        return signals

    def _extract_signal_from_analysis(
        self, agent_id: str, analysis: dict, symbol: str, display_name: str | None = None
    ) -> dict:
        """
        Extract standardized signal from agent analysis.

        Parameters
        ----------
        agent_id : str
            Agent identifier
        analysis : dict
            Analysis data from agent
        symbol : str
            Trading symbol
        display_name : str | None
            Human-readable agent name

        Returns
        -------
        dict
            Standardized signal with action, direction, sentiment, confidence, reasoning
        """
        # Extract signal components with priority order
        # 1. Check for 'action' field (Portfolio Manager)
        # 2. Check for 'signal' field (Risk Manager, Trader Agent)
        # 3. Check for 'recommendation' field (Technical Agent)
        raw_signal = (
            analysis.get("action") or analysis.get("signal") or analysis.get("recommendation") or "hold"
        ).upper()

        # Extract direction if available (Portfolio Manager)
        direction = analysis.get("direction", "").upper()

        confidence = analysis.get("confidence", 0.5)

        # Normalize confidence to 0-1 range (agents may return 0-100)
        if confidence > 1.0:
            confidence = confidence / 100.0

        # Map signal to standardized action and direction
        # Support: BUY/SELL/HOLD, LONG/SHORT, STRONG_BUY/STRONG_SELL
        action_map = {
            # Standard buy/sell signals
            "BUY": ("buy", "LONG"),
            "STRONG_BUY": ("buy", "LONG"),
            "SELL": ("sell", "SHORT"),
            "STRONG_SELL": ("sell", "SHORT"),
            "HOLD": ("hold", "NONE"),
            "NEUTRAL": ("hold", "NONE"),
            # Futures-specific signals
            "LONG": ("buy", "LONG"),
            "SHORT": ("sell", "SHORT"),
        }

        # Get action and default direction from mapping
        action, default_direction = action_map.get(raw_signal, ("hold", "NONE"))

        # Use explicit direction if provided, otherwise use mapped direction
        if not direction or direction == "NONE":
            direction = default_direction

        # Determine sentiment from direction (more accurate for futures trading)
        sentiment_map = {
            "LONG": "bullish",
            "SHORT": "bearish",
            "NONE": "neutral",
        }
        sentiment = sentiment_map.get(direction, "neutral")

        # Extract reasoning (look in multiple possible fields)
        reasoning = (
            analysis.get("reasoning")
            or analysis.get("analysis")
            or analysis.get("message")
            or f"Analysis performed for {symbol}"
        )

        # Extract additional futures-specific fields if available
        leverage = analysis.get("leverage") or analysis.get("suggested_leverage")
        stop_loss = analysis.get("stop_loss")
        position_size = analysis.get("position_size")

        signal = {
            "action": action,
            "direction": direction,  # LONG, SHORT, or NONE
            "sentiment": sentiment,
            "confidence": confidence,
            "reasoning": reasoning,
            "agent_display_name": display_name or agent_id.replace("_", " ").title(),
        }

        # Add optional futures trading fields if present
        if leverage:
            signal["leverage"] = leverage
        if stop_loss:
            signal["stop_loss"] = stop_loss
        if position_size:
            signal["position_size"] = position_size

        return signal

    async def adetermine_consensus(  # noqa: PLR0912, PLR0915
        self,
        council_id: int,
        signals: dict[str, dict[str, dict]],
        threshold: float = 0.6,
        council_run_id: int | None = None,
        council_run_cycle_id: int | None = None,
    ) -> list[dict]:
        """
        Determine consensus from agent signals for each symbol using futures trading logic.

        For each symbol, analyzes agent votes for LONG/SHORT positions and determines
        consensus based on threshold. Supports futures trading with directional positions.

        Parameters
        ----------
        council_id : int
            Council ID
        signals : dict[str, dict[str, dict]]
            Agent signals structured as signals[symbol][agent_id] = {action, direction, confidence, ...}
            Each signal should contain:
            - action: "buy", "sell", or "hold"
            - direction: "LONG", "SHORT", or "NONE"
            - confidence: float (0.0-1.0)
        threshold : float
            Consensus threshold (0.0-1.0). Default is 0.6 (60% agreement).
            E.g., 0.6 means 60% of agents must vote LONG for BUY consensus.
        council_run_id : int | None
            Council run ID for tracking
        council_run_cycle_id : int | None
            Council run cycle ID for tracking

        Returns
        -------
        list[dict]
            List of consensus decisions, one per symbol, each with keys:
            - decision: str (BUY, SELL, HOLD)
            - direction: str (LONG, SHORT, NONE)
            - symbol: str
            - confidence: float (average agent confidence)
            - agent_votes: dict[agent_id, vote] (e.g., {"agent1": "LONG", "agent2": "SHORT"})
            - vote_counts: dict (e.g., {"long": 3, "short": 1, "hold": 0})
            - council_run_id: int | None
            - council_run_cycle_id: int | None
            - consensus_decision_id: int
        """
        if not signals:
            logger.warning("No signals provided for consensus determination", council_id=council_id)
            return []

        logger.info("Determining consensus per symbol", symbols=list(signals.keys()))

        consensuses = []

        # Process each symbol independently
        for symbol, agents_dict in signals.items():
            if not agents_dict:
                logger.warning("No agent signals for symbol, skipping", symbol=symbol)
                continue

            # Count votes for this symbol using direction (more accurate for futures)
            votes = {"long": 0, "short": 0, "hold": 0}
            agent_votes = {}
            total_confidence = 0.0

            for agent_id, signal in agents_dict.items():
                # Use direction field (LONG/SHORT/NONE) for futures trading
                direction = signal.get("direction", "").upper()

                # Fallback to action if direction not available
                if not direction or direction == "NONE":
                    action = signal.get("action", "hold").lower()
                    if action == "buy":
                        direction = "LONG"
                    elif action == "sell":
                        direction = "SHORT"
                    else:
                        direction = "NONE"

                confidence = signal.get("confidence", 0.5)

                # Map direction to vote category
                if direction == "LONG":
                    votes["long"] += 1
                    agent_votes[agent_id] = "LONG"
                elif direction == "SHORT":
                    votes["short"] += 1
                    agent_votes[agent_id] = "SHORT"
                else:
                    votes["hold"] += 1
                    agent_votes[agent_id] = "HOLD"

                total_confidence += confidence

            # Determine majority for this symbol based on LONG/SHORT votes
            total_votes = sum(votes.values())
            decision = "HOLD"
            direction = "NONE"

            if total_votes > 0:
                long_ratio = votes["long"] / total_votes
                short_ratio = votes["short"] / total_votes

                if long_ratio >= threshold:
                    decision = "BUY"
                    direction = "LONG"
                elif short_ratio >= threshold:
                    decision = "SELL"
                    direction = "SHORT"
                else:
                    decision = "HOLD"
                    direction = "NONE"

            avg_confidence = total_confidence / len(agents_dict) if agents_dict else 0.0

            # Store consensus message for this symbol
            await self.repo.create_debate_message(
                council_id=council_id,
                agent_name="System",
                message=(
                    f"Consensus for {symbol}: {decision} ({direction}). "
                    f"Votes: {votes['long']} LONG, {votes['short']} SHORT, {votes['hold']} HOLD. "
                    f"Confidence: {avg_confidence:.2%}"
                ),
                message_type="consensus",
                sentiment=("bullish" if direction == "LONG" else "bearish" if direction == "SHORT" else "neutral"),
                market_symbol=symbol,
                confidence=Decimal(str(avg_confidence)),
                debate_round=1,
            )

            # Store consensus decision record for this symbol
            reasoning = (
                f"Consensus reached for {symbol} with {decision} ({direction}) decision. "
                f"Agent votes: {votes['long']} LONG, {votes['short']} SHORT, {votes['hold']} HOLD. "
                f"Average confidence: {avg_confidence:.2%}. "
                f"Threshold: {threshold:.0%}"
            )

            consensus_record = await self.repo.create_consensus_decision(
                council_id=council_id,
                decision=decision,
                symbol=symbol,
                confidence=avg_confidence,
                votes_buy=votes["long"],  # Map LONG votes to votes_buy
                votes_sell=votes["short"],  # Map SHORT votes to votes_sell
                votes_hold=votes["hold"],
                agent_votes=agent_votes,
                council_run_id=council_run_id,
                council_run_cycle_id=council_run_cycle_id,
                reasoning=reasoning,
                was_executed=False,
                execution_reason="pending" if decision != "HOLD" else "hold_decision",
            )

            consensus = {
                "decision": decision,
                "direction": direction,  # LONG, SHORT, or NONE
                "symbol": symbol,
                "confidence": avg_confidence,
                "agent_votes": agent_votes,
                "vote_counts": votes,
                "council_run_id": council_run_id,
                "council_run_cycle_id": council_run_cycle_id,
                "consensus_decision_id": consensus_record.id,
            }

            consensuses.append(consensus)

            logger.info(
                "Consensus determined for symbol",
                council_id=council_id,
                symbol=symbol,
                decision=decision,
                direction=direction,
                confidence=avg_confidence,
                votes=votes,
                consensus_decision_id=consensus_record.id,
            )

        logger.info(
            "Total consensuses determined",
            council_id=council_id,
            total_consensuses=len(consensuses),
            symbols=[c["symbol"] for c in consensuses],
        )

        return consensuses
