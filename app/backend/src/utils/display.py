import json
import os
import subprocess
from typing import Any

import structlog
from colorama import Fore, Style
from tabulate import tabulate

from .analysts import get_crypto_agents_list

logger = structlog.get_logger(__name__)

# Display control - can be overridden for testing
DISPLAY_ENABLED = True


def _display(_text: str) -> None:
    """Display text if display is enabled."""
    if DISPLAY_ENABLED:
        pass


def sort_agent_signals(signals):
    """Sort agent signals in a consistent order."""
    # Create order mapping from crypto agents
    crypto_agents = get_crypto_agents_list()

    # Create a mapping from agent keys to their order
    # The keys are like "satoshi_nakamoto", "vitalik_buterin", etc.
    agent_key_order = {}
    for idx, agent in enumerate(crypto_agents):
        key = agent["key"]
        # Convert key to display format to match what's in the signals
        display_name = key.replace("_agent", "").replace("_", " ").title()
        agent_key_order[display_name] = idx

    # Add Risk Management at the end if needed
    agent_key_order["Crypto Risk Management"] = len(crypto_agents)

    # Sort signals by their position in the agent key order
    return sorted(signals, key=lambda x: agent_key_order.get(x[0], 999))


def print_trading_output(result: dict) -> None:
    """
    Print formatted trading results with colored tables for multiple crypto symbols.

    Args:
        result (dict): Dictionary containing decisions and analyst signals for multiple crypto symbols
    """
    decisions = result.get("decisions")
    if not decisions:
        _display(f"{Fore.RED}No trading decisions available{Style.RESET_ALL}")
        return

    # Print decisions for each crypto symbol
    for symbol, decision in decisions.items():
        _display(f"\n{Fore.WHITE}{Style.BRIGHT}Analysis for {Fore.CYAN}{symbol}{Style.RESET_ALL}")
        _display(f"{Fore.WHITE}{Style.BRIGHT}{'=' * 50}{Style.RESET_ALL}")

        # Prepare analyst signals table for this symbol
        table_data = []
        for agent, signals in result.get("analyst_signals", {}).items():
            if symbol not in signals:
                continue

            # Skip Risk Management agent in the signals section
            if agent == "crypto_risk_management_agent":
                continue

            signal = signals[symbol]
            agent_name = agent.replace("_agent", "").replace("_", " ").title()
            signal_type = signal.get("signal", "").upper()
            confidence = signal.get("confidence", 0)

            signal_color = {
                "STRONG_BUY": Fore.GREEN,
                "BUY": Fore.GREEN,
                "HOLD": Fore.YELLOW,
                "SELL": Fore.RED,
                "STRONG_SELL": Fore.RED,
            }.get(signal_type, Fore.WHITE)

            # Get reasoning if available
            reasoning_str = ""
            if signal.get("reasoning"):
                reasoning = signal["reasoning"]

                # Handle different types of reasoning (string, dict, etc.)
                if isinstance(reasoning, str):
                    reasoning_str = reasoning
                elif isinstance(reasoning, dict):
                    # Convert dict to string representation
                    reasoning_str = json.dumps(reasoning, indent=2)
                else:
                    # Convert any other type to string
                    reasoning_str = str(reasoning)

                # Wrap long reasoning text to make it more readable
                wrapped_reasoning = ""
                current_line = ""
                # Use a fixed width of 60 characters to match the table column width
                max_line_length = 60
                for word in reasoning_str.split():
                    if len(current_line) + len(word) + 1 > max_line_length:
                        wrapped_reasoning += current_line + "\n"
                        current_line = word
                    elif current_line:
                        current_line += " " + word
                    else:
                        current_line = word
                if current_line:
                    wrapped_reasoning += current_line

                reasoning_str = wrapped_reasoning

            table_data.append(
                [
                    f"{Fore.CYAN}{agent_name}{Style.RESET_ALL}",
                    f"{signal_color}{signal_type}{Style.RESET_ALL}",
                    f"{Fore.WHITE}{confidence}%{Style.RESET_ALL}",
                    f"{Fore.WHITE}{reasoning_str}{Style.RESET_ALL}",
                ]
            )

        # Sort the signals according to the predefined order
        table_data = sort_agent_signals(table_data)

        _display(
            f"\n{Fore.WHITE}{Style.BRIGHT}AGENT ANALYSIS:{Style.RESET_ALL} [{Fore.CYAN}{symbol}{Style.RESET_ALL}]"
        )
        _display(
            tabulate(
                table_data,
                headers=[f"{Fore.WHITE}Agent", "Signal", "Confidence", "Reasoning"],
                tablefmt="grid",
                colalign=("left", "center", "right", "left"),
            )
        )

        # Print Futures Trading Decision Table
        action = decision.get("action", "").upper()
        direction = decision.get("direction", "").upper()
        leverage = decision.get("leverage", 1.0)
        position_size = decision.get("position_size", 0)

        # Color based on direction for futures
        if direction == "LONG":
            action_color = Fore.GREEN
            direction_display = f"{Fore.GREEN}LONG{Style.RESET_ALL}"
        elif direction == "SHORT":
            action_color = Fore.RED
            direction_display = f"{Fore.RED}SHORT{Style.RESET_ALL}"
        else:
            action_color = {
                "BUY": Fore.GREEN,
                "SELL": Fore.RED,
                "HOLD": Fore.YELLOW,
            }.get(action, Fore.WHITE)
            direction_display = f"{Fore.YELLOW}N/A{Style.RESET_ALL}"

        # Get reasoning and format it
        reasoning = decision.get("reasoning", "")
        # Wrap long reasoning text to make it more readable
        wrapped_reasoning = ""
        if reasoning:
            current_line = ""
            # Use a fixed width of 60 characters to match the table column width
            max_line_length = 60
            for word in reasoning.split():
                if len(current_line) + len(word) + 1 > max_line_length:
                    wrapped_reasoning += current_line + "\n"
                    current_line = word
                elif current_line:
                    current_line += " " + word
                else:
                    current_line = word
            if current_line:
                wrapped_reasoning += current_line

        confidence = decision.get("confidence")
        confidence_str = f"{confidence:.1f}%" if confidence is not None else "N/A"

        # Build futures-focused decision data
        decision_data = [
            ["Action", f"{action_color}{action}{Style.RESET_ALL}"],
            ["Direction", direction_display],
            ["Leverage", f"{Fore.CYAN}{leverage}x{Style.RESET_ALL}"],
            ["Position Size", f"{Fore.YELLOW}${position_size:.2f}{Style.RESET_ALL}"],
            ["Quantity", f"{action_color}{decision.get('quantity', 0):.6f}{Style.RESET_ALL}"],
            [
                "Confidence",
                f"{Fore.WHITE}{confidence_str}{Style.RESET_ALL}",
            ],
            ["Reasoning", f"{Fore.WHITE}{wrapped_reasoning}{Style.RESET_ALL}"],
        ]

        _display(
            f"\n{Fore.WHITE}{Style.BRIGHT}FUTURES TRADING DECISION:{Style.RESET_ALL} "
            f"[{Fore.CYAN}{symbol}{Style.RESET_ALL}]"
        )
        _display(tabulate(decision_data, tablefmt="grid", colalign=("left", "left")))

    # Print Portfolio Summary
    _display(f"\n{Fore.WHITE}{Style.BRIGHT}PORTFOLIO SUMMARY:{Style.RESET_ALL}")
    portfolio_data = []

    # Extract portfolio manager reasoning (common for all symbols)
    portfolio_manager_reasoning = None
    for decision in decisions.values():
        if decision.get("reasoning"):
            portfolio_manager_reasoning = decision.get("reasoning")
            break

    analyst_signals = result.get("analyst_signals", {})
    for symbol, decision in decisions.items():
        action = decision.get("action", "").upper()
        action_color = {
            "BUY": Fore.GREEN,
            "SELL": Fore.RED,
            "HOLD": Fore.YELLOW,
        }.get(action, Fore.WHITE)

        # Calculate analyst signal counts
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        if analyst_signals:
            for signals in analyst_signals.values():
                if symbol in signals:
                    signal = signals[symbol].get("signal", "").upper()
                    if signal in ["STRONG_BUY", "BUY"]:
                        bullish_count += 1
                    elif signal in ["STRONG_SELL", "SELL"]:
                        bearish_count += 1
                    elif signal == "HOLD":
                        neutral_count += 1

        confidence = decision.get("confidence")
        confidence_str = f"{confidence:.1f}%" if confidence is not None else "N/A"

        portfolio_data.append(
            [
                f"{Fore.CYAN}{symbol}{Style.RESET_ALL}",
                f"{action_color}{action}{Style.RESET_ALL}",
                f"{action_color}{decision.get('quantity', 0)}{Style.RESET_ALL}",
                f"{Fore.WHITE}{confidence_str}{Style.RESET_ALL}",
                f"{Fore.GREEN}{bullish_count}{Style.RESET_ALL}",
                f"{Fore.RED}{bearish_count}{Style.RESET_ALL}",
                f"{Fore.YELLOW}{neutral_count}{Style.RESET_ALL}",
            ]
        )

    headers = [
        f"{Fore.WHITE}Symbol",
        f"{Fore.WHITE}Action",
        f"{Fore.WHITE}Quantity",
        f"{Fore.WHITE}Confidence",
        f"{Fore.WHITE}Bullish",
        f"{Fore.WHITE}Bearish",
        f"{Fore.WHITE}Neutral",
    ]

    # Print the portfolio summary table
    _display(
        tabulate(
            portfolio_data,
            headers=headers,
            tablefmt="grid",
            colalign=("left", "center", "right", "right", "center", "center", "center"),
        )
    )

    # Print Portfolio Manager's reasoning if available
    if portfolio_manager_reasoning:
        # Handle different types of reasoning (string, dict, etc.)
        reasoning_str = ""
        if isinstance(portfolio_manager_reasoning, str):
            reasoning_str = portfolio_manager_reasoning
        elif isinstance(portfolio_manager_reasoning, dict):
            # Convert dict to string representation
            reasoning_str = json.dumps(portfolio_manager_reasoning, indent=2)
        else:
            # Convert any other type to string
            reasoning_str = str(portfolio_manager_reasoning)

        # Wrap long reasoning text to make it more readable
        wrapped_reasoning = ""
        current_line = ""
        # Use a fixed width of 60 characters to match the table column width
        max_line_length = 60
        for word in reasoning_str.split():
            if len(current_line) + len(word) + 1 > max_line_length:
                wrapped_reasoning += current_line + "\n"
                current_line = word
            elif current_line:
                current_line += " " + word
            else:
                current_line = word
        if current_line:
            wrapped_reasoning += current_line

        _display(f"\n{Fore.WHITE}{Style.BRIGHT}Portfolio Strategy:{Style.RESET_ALL}")
        _display(f"{Fore.CYAN}{wrapped_reasoning}{Style.RESET_ALL}")


def print_backtest_results(table_rows: list) -> None:
    """Print the backtest results in a nicely formatted table."""
    # Clear the screen
    clear_cmd = "cls" if os.name == "nt" else "clear"
    subprocess.run([clear_cmd], check=False)  # noqa: S603

    # Split rows into ticker rows and summary rows
    ticker_rows = []
    summary_rows = []

    for row in table_rows:
        if isinstance(row[1], str) and "PORTFOLIO SUMMARY" in row[1]:
            summary_rows.append(row)
        else:
            ticker_rows.append(row)

    # Display latest portfolio summary
    if summary_rows:
        # Pick the most recent summary by date (YYYY-MM-DD)
        latest_summary = max(summary_rows, key=lambda r: r[0])
        _display(f"\n{Fore.WHITE}{Style.BRIGHT}PORTFOLIO SUMMARY:{Style.RESET_ALL}")

        # Adjusted indexes after adding Long/Short Shares
        position_str = latest_summary[7].split("$")[1].split(Style.RESET_ALL)[0].replace(",", "")
        cash_str = latest_summary[8].split("$")[1].split(Style.RESET_ALL)[0].replace(",", "")
        total_str = latest_summary[9].split("$")[1].split(Style.RESET_ALL)[0].replace(",", "")

        _display(f"Cash Balance: {Fore.CYAN}${float(cash_str):,.2f}{Style.RESET_ALL}")
        _display(f"Total Position Value: {Fore.YELLOW}${float(position_str):,.2f}{Style.RESET_ALL}")
        _display(f"Total Value: {Fore.WHITE}${float(total_str):,.2f}{Style.RESET_ALL}")
        _display(f"Portfolio Return: {latest_summary[10]}")
        if len(latest_summary) > 14 and latest_summary[14]:
            _display(f"Benchmark Return: {latest_summary[14]}")

        # Display performance metrics if available
        if latest_summary[11]:  # Sharpe ratio
            _display(f"Sharpe Ratio: {latest_summary[11]}")
        if latest_summary[12]:  # Sortino ratio
            _display(f"Sortino Ratio: {latest_summary[12]}")
        if latest_summary[13]:  # Max drawdown
            _display(f"Max Drawdown: {latest_summary[13]}")

    # Add vertical spacing
    _display("\n" * 2)

    # Print the table with just ticker rows
    _display(
        tabulate(
            ticker_rows,
            headers=[
                "Date",
                "Ticker",
                "Action",
                "Quantity",
                "Price",
                "Long Shares",
                "Short Shares",
                "Position Value",
            ],
            tablefmt="grid",
            colalign=(
                "left",  # Date
                "left",  # Ticker
                "center",  # Action
                "right",  # Quantity
                "right",  # Price
                "right",  # Long Shares
                "right",  # Short Shares
                "right",  # Position Value
            ),
        )
    )

    # Add vertical spacing
    _display("\n" * 4)


def format_backtest_row(
    date: str,
    ticker: str,
    action: str,
    quantity: float,
    price: float,
    long_shares: float = 0,
    short_shares: float = 0,
    position_value: float = 0,
    *,
    is_summary: bool = False,
    total_value: float | None = None,
    return_pct: float | None = None,
    cash_balance: float | None = None,
    total_position_value: float | None = None,
    sharpe_ratio: float | None = None,
    sortino_ratio: float | None = None,
    max_drawdown: float | None = None,
    benchmark_return_pct: float | None = None,
) -> list[Any]:
    """Format a row for the backtest results table."""
    # Color the action
    action_color = {
        "BUY": Fore.GREEN,
        "COVER": Fore.GREEN,
        "SELL": Fore.RED,
        "SHORT": Fore.RED,
        "HOLD": Fore.WHITE,
    }.get(action.upper(), Fore.WHITE)

    if is_summary:
        return_color = Fore.GREEN if return_pct and return_pct >= 0 else Fore.RED
        benchmark_str = ""
        if benchmark_return_pct is not None:
            bench_color = Fore.GREEN if benchmark_return_pct >= 0 else Fore.RED
            benchmark_str = f"{bench_color}{benchmark_return_pct:+.2f}%{Style.RESET_ALL}"
        return [
            date,
            f"{Fore.WHITE}{Style.BRIGHT}PORTFOLIO SUMMARY{Style.RESET_ALL}",
            "",  # Action
            "",  # Quantity
            "",  # Price
            "",  # Long Shares
            "",  # Short Shares
            f"{Fore.YELLOW}${total_position_value:,.2f}{Style.RESET_ALL}",  # Total Position Value
            f"{Fore.CYAN}${cash_balance:,.2f}{Style.RESET_ALL}",  # Cash Balance
            f"{Fore.WHITE}${total_value:,.2f}{Style.RESET_ALL}",  # Total Value
            f"{return_color}{return_pct:+.2f}%{Style.RESET_ALL}",  # Return
            f"{Fore.YELLOW}{sharpe_ratio:.2f}{Style.RESET_ALL}" if sharpe_ratio is not None else "",  # Sharpe Ratio
            f"{Fore.YELLOW}{sortino_ratio:.2f}{Style.RESET_ALL}" if sortino_ratio is not None else "",  # Sortino Ratio
            f"{Fore.RED}{max_drawdown:.2f}%{Style.RESET_ALL}"
            if max_drawdown is not None
            else "",  # Max Drawdown (signed)
            benchmark_str,  # Benchmark (S&P 500)
        ]
    return [
        date,
        f"{Fore.CYAN}{ticker}{Style.RESET_ALL}",
        f"{action_color}{action.upper()}{Style.RESET_ALL}",
        f"{action_color}{quantity:,.0f}{Style.RESET_ALL}",
        f"{Fore.WHITE}{price:,.2f}{Style.RESET_ALL}",
        f"{Fore.GREEN}{long_shares:,.0f}{Style.RESET_ALL}",  # Long Shares
        f"{Fore.RED}{short_shares:,.0f}{Style.RESET_ALL}",  # Short Shares
        f"{Fore.YELLOW}{position_value:,.2f}{Style.RESET_ALL}",
    ]
