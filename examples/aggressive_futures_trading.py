"""Example script for aggressive futures trading with the enhanced agents."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import click
import structlog

from app.backend.src.agents import CryptoAgent, FuturesTradingAgent

logger = structlog.get_logger(__name__)


def format_price(value: float | None) -> str:
    """Format a numeric price for display, handling missing values.

    Parameters
    ----------
    value : float | None
        Price value to format.

    Returns
    -------
    str
        Formatted price string or "N/A" if the value is missing.
    """

    if value is None:
        return "N/A"
    return f"${value:.2f}"


def build_llm_portfolio_snapshot(raw_portfolio: dict) -> dict:
    """Convert Binance portfolio to the compact state expected by the LLM.

    Shape:
      {
        "cash": float,                    # available margin
        "total_value": float,            # total account value
        "unrealized_pnl": float,
        "available_margin": float,       # alias for cash
        "positions": {                   # map by symbol
          "BTCUSDT": {
             "long": float,             # amount (if long)
             "short": float,            # amount (if short)
             "current_price": float,    # mark price
             "leverage": int
          },
          ...
        }
      }
    """
    cash = float(raw_portfolio.get("cash", 0.0))
    total_value = float(raw_portfolio.get("total_balance", 0.0))
    unrealized_pnl = float(raw_portfolio.get("unrealized_pnl", 0.0))

    positions_list = raw_portfolio.get("positions", []) or []
    positions_map: dict[str, dict] = {}

    for p in positions_list:
        symbol = p.get("symbol")
        if not symbol:
            continue

        amount = float(p.get("amount", 0.0))
        position_side = str(p.get("position_side", "BOTH"))
        mark_price = float(p.get("mark_price", 0.0))
        leverage = int(p.get("leverage", 1) or 1)

        entry = positions_map.setdefault(symbol, {"long": 0.0, "short": 0.0})

        # Normalize into long/short buckets; handle BOTH by sign of amount
        if position_side.upper() == "LONG" or (
            position_side.upper() == "BOTH" and amount >= 0
        ):
            entry["long"] = abs(amount)
        elif position_side.upper() == "SHORT" or (
            position_side.upper() == "BOTH" and amount < 0
        ):
            entry["short"] = abs(amount)

        entry["current_price"] = mark_price
        entry["leverage"] = leverage

    return {
        "cash": cash,
        "total_value": total_value,
        "unrealized_pnl": unrealized_pnl,
        "available_margin": cash,
        "positions": positions_map,
    }


@click.group()
def cli():
    """
    Aggressive Futures Trading CLI.

    A command-line tool for running AI-powered cryptocurrency futures trading
    strategies with customizable models and real-time execution on Binance Futures.
    """


@cli.command()
@click.option(
    "--symbols",
    "-s",
    default="BTCUSDT,ETHUSDT,SOLUSDT",
    help="Comma-separated list of trading symbols (e.g., BTCUSDT,ETHUSDT)",
    show_default=True,
)
@click.option(
    "--model-name",
    "-m",
    default="gpt-5",
    help="LLM model name for AI agents",
    show_default=True,
)
@click.option(
    "--model-provider",
    "-p",
    default="LiteLLM",
    help="Model provider (LiteLLM, OPENAI, ANTHROPIC, etc.)",
    show_default=True,
)
def trade(symbols: str, model_name: str, model_provider: str):
    """
    Run aggressive futures trading workflow.

    This command:
    - Fetches current portfolio state from Binance Futures
    - Gets AI trading decisions for specified symbols
    - Executes LONG/SHORT positions with stop-losses
    - Displays results and final portfolio state

    Example:
        python examples/aggressive_futures_trading.py trade -s BTCUSDT,ETHUSDT -m gpt-4
    """
    symbol_list = [s.strip() for s in symbols.split(",")]

    async def run():
        """Execute the trading workflow."""
        # Initialize agents
        logger.info(
            "Initializing trading agents",
            model_name=model_name,
            model_provider=model_provider,
        )

        # AI decision-making agent
        crypto_agent = CryptoAgent(
            model_name=model_name,
            model_provider=model_provider,
        )

        # Futures execution agent
        futures_agent = FuturesTradingAgent(enable_rate_limiting=True)

        # Get current portfolio state from Binance
        logger.info("Fetching portfolio state from Binance Futures...")
        portfolio = await futures_agent.get_portfolio_state()

        logger.info(
            "Portfolio state",
            available_margin=portfolio["cash"],
            total_balance=portfolio["total_balance"],
            unrealized_pnl=portfolio["unrealized_pnl"],
            position_count=portfolio["position_count"],
        )

        # Get AI trading decisions
        logger.info("Getting AI trading decisions...", symbols=symbol_list)

        # Pass a compact portfolio snapshot as the initial LLM state
        llm_portfolio = build_llm_portfolio_snapshot(portfolio)

        results = crypto_agent.run(
            tickers=symbol_list,
            end_date=datetime.now(),
            portfolio=llm_portfolio,
        )

        # Process decisions
        logger.info("Processing trading decisions...")

        for symbol in symbol_list:
            decision = results["decisions"].get(symbol, {})

            if not decision:
                logger.warning("No decision for symbol", symbol=symbol)
                continue

            logger.info(
                "Trading decision",
                symbol=symbol,
                action=decision.get("action", "hold"),
                confidence=decision.get("confidence", 0),
                leverage=decision.get("leverage", 1),
                reasoning=decision.get("reasoning", ""),
            )

            # Execute decision
            if decision.get("action") != "hold":
                logger.info("Getting ready to execute trade", symbol=symbol)
                # Calculate current exposure
                current_positions = await futures_agent.aget_positions()
                total_position_value = sum(
                    abs(pos["amount"]) * pos["mark_price"] for pos in current_positions
                )
                current_exposure = (
                    total_position_value / portfolio["total_balance"]
                    if portfolio["total_balance"] > 0
                    else 0.0
                )

                logger.info(
                    "Executing trade details",
                    symbol=symbol,
                    current_exposure=current_exposure,
                )
                # Execute
                result = await futures_agent.execute_trading_decision(
                    symbol=symbol,
                    decision=decision,
                    portfolio_value=portfolio["total_balance"],
                    current_exposure=current_exposure,
                )

                logger.info(
                    "Execution result",
                    symbol=symbol,
                    status=result["status"],
                    order_id=result.get("order_id"),
                    price=result.get("price"),
                    stop_loss_price=result.get("stop_loss_price"),
                )

                if result["status"] == "success":
                    click.echo(
                        f"\n✅ {symbol}: {decision['action'].upper()} position opened"
                    )
                    click.echo(f"   Order ID: {result['order_id']}")
                    click.echo(f"   Entry Price: {format_price(result.get('price'))}")
                    click.echo(f"   Leverage: {decision.get('leverage', 1)}x")

                    # Display Stop Loss information
                    stop_loss_price = result.get("stop_loss_price")
                    if stop_loss_price is not None:
                        sl_order_id = result.get("stop_loss_order_id", "N/A")
                        click.echo(
                            f"   Stop Loss: {format_price(stop_loss_price)} (Order: {sl_order_id})"
                        )
                    else:
                        pending_stop = decision.get("stop_loss")
                        if pending_stop is not None:
                            click.echo(
                                f"   Stop Loss: {format_price(pending_stop)} (Pending)"
                            )

                    # Display Take Profit information
                    if "take_profit_orders" in result:
                        click.echo("   Take Profit Levels:")
                        for tp in result["take_profit_orders"]:
                            tp_price = tp.get("price")
                            if tp_price is None:
                                continue
                            click.echo(
                                f"     • {tp['level'].upper()}: {format_price(tp_price)} (Order: {tp['order_id']})"
                            )
                    elif any(
                        key in decision
                        for key in [
                            "take_profit_short",
                            "take_profit_mid",
                            "take_profit_long",
                        ]
                    ):
                        take_profit_levels = [
                            ("SHORT", decision.get("take_profit_short")),
                            ("MID", decision.get("take_profit_mid")),
                            ("LONG", decision.get("take_profit_long")),
                        ]
                        printed_header = False
                        for label, price in take_profit_levels:
                            if price is None:
                                continue
                            if not printed_header:
                                click.echo("   Take Profit Levels:")
                                printed_header = True
                            click.echo(f"     • {label}: {format_price(price)}")

                    click.echo(f"   Reasoning: {decision.get('reasoning', 'N/A')}\n")
                else:
                    click.echo(
                        f"\n❌ {symbol}: {result['status']} - {result.get('reason', 'Unknown error')}\n"
                    )

        # Display final portfolio state
        logger.info("Fetching updated portfolio state...")
        final_portfolio = await futures_agent.get_portfolio_state()

        click.echo("\n" + "=" * 60)
        click.echo("FINAL PORTFOLIO STATE")
        click.echo("=" * 60)
        click.echo(f"Available Margin: ${final_portfolio['cash']:.2f}")
        click.echo(f"Total Balance: ${final_portfolio['total_balance']:.2f}")
        click.echo(f"Unrealized PnL: ${final_portfolio['unrealized_pnl']:.2f}")
        click.echo(f"Active Positions: {final_portfolio['position_count']}")

        if final_portfolio["positions"]:
            click.echo("\nPositions:")
            for pos in final_portfolio["positions"]:
                click.echo(f"  {pos['symbol']}:")
                click.echo(f"    Amount: {pos['amount']}")
                click.echo(f"    Entry: ${pos['entry_price']}")
                click.echo(f"    Mark: ${pos['mark_price']}")
                click.echo(f"    PnL: ${pos['unrealized_pnl']:.2f}")
                click.echo(f"    Leverage: {pos['leverage']}x")

        click.echo("=" * 60 + "\n")

    asyncio.run(run())


@cli.command()
@click.option(
    "--confirm",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def close(confirm: bool):
    """
    Close all open positions.

    This command will close all active futures positions at market price.
    Use with caution as this action cannot be undone.

    Example:
        python examples/aggressive_futures_trading.py close -y
    """
    if not confirm:
        click.confirm(
            "⚠️  This will close ALL open positions. Are you sure?",
            abort=True,
        )

    async def run():
        """Close all positions."""
        logger.info("Closing all positions...")

        futures_agent = FuturesTradingAgent()

        # Get current positions
        positions = await futures_agent.service.aget_positions()

        if not positions:
            click.echo("No open positions to close.")
            return

        click.echo(f"\nClosing {len(positions)} position(s)...")

        for pos in positions:
            symbol = pos["symbol"]
            position_side = pos.get("position_side", "BOTH")

            logger.info("Closing position", symbol=symbol, position_side=position_side)

            result = await futures_agent.close_position(symbol, position_side)

            if result["status"] == "success":
                click.echo(
                    click.style(
                        f"✅ {symbol} closed: Order {result['order_id']}", fg="green"
                    )
                )
            else:
                click.echo(
                    click.style(
                        f"❌ {symbol} failed: {result.get('reason', 'Unknown error')}",
                        fg="red",
                    )
                )

    asyncio.run(run())


@cli.command()
@click.option(
    "--watch",
    "-w",
    is_flag=True,
    help="Watch mode: continuously monitor positions (updates every 10s)",
)
def monitor(watch: bool):
    """
    Monitor open positions and PnL.

    This command displays current portfolio performance including:
    - Available margin and total balance
    - Unrealized PnL for all positions
    - Individual position details (entry, mark price, leverage)

    Use --watch/-w for continuous monitoring.

    Example:
        python examples/aggressive_futures_trading.py monitor --watch
    """

    async def run_once():
        """Display current positions once."""
        futures_agent = FuturesTradingAgent()

        portfolio = await futures_agent.get_portfolio_state()
        positions = portfolio["positions"]

        click.clear()
        click.echo("\n" + "=" * 60)
        click.echo("POSITION MONITOR")
        click.echo("=" * 60)
        click.echo(f"Available Margin: ${portfolio['cash']:.2f}")
        click.echo(f"Total Balance: ${portfolio['total_balance']:.2f}")

        # Color-code PnL
        pnl = portfolio["unrealized_pnl"]
        pnl_color = "green" if pnl > 0 else "red" if pnl < 0 else "white"
        click.echo(
            "Unrealized PnL: " + click.style(f"${pnl:.2f}", fg=pnl_color, bold=True)
        )

        click.echo(f"Active Positions: {len(positions)}")
        click.echo("-" * 60)

        if not positions:
            click.echo("No open positions.")
        else:
            for pos in positions:
                pnl_pct = (
                    (pos["unrealized_pnl"] / (pos["entry_price"] * abs(pos["amount"])))
                    * 100
                    if pos["entry_price"] > 0
                    else 0
                )
                pos_pnl = pos["unrealized_pnl"]
                pnl_color = "green" if pos_pnl > 0 else "red"

                click.echo(f"\n{click.style(pos['symbol'], bold=True)}:")
                click.echo(f"  Side: {pos['position_side']}")
                click.echo(f"  Amount: {pos['amount']}")
                click.echo(f"  Entry Price: ${pos['entry_price']:.2f}")
                click.echo(f"  Mark Price: ${pos['mark_price']:.2f}")
                click.echo(
                    "  PnL: "
                    + click.style(
                        f"${pos_pnl:.2f} ({pnl_pct:+.2f}%)",
                        fg=pnl_color,
                        bold=True,
                    )
                )
                click.echo(f"  Leverage: {pos['leverage']}x")

        click.echo("=" * 60 + "\n")

        if watch:
            click.echo("(Press Ctrl+C to stop watching)")

    if watch:
        import time

        try:
            while True:
                asyncio.run(run_once())
                time.sleep(10)
        except KeyboardInterrupt:
            click.echo("\n👋 Stopped monitoring.")
    else:
        asyncio.run(run_once())


if __name__ == "__main__":
    cli()
