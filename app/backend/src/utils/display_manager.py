"""Display manager for trading output with JSON and beauty modes."""

import json
import os
import subprocess
from enum import Enum

import structlog
from colorama import Fore, Style, init
from tabulate import tabulate

# Initialize colorama
init(autoreset=True)

logger = structlog.get_logger(__name__)


class DisplayMode(Enum):
    """Display output mode."""

    JSON = "json"
    BEAUTY = "beauty"


class DisplayManager:
    """Manager for trading output display with multiple formats."""

    def __init__(self, mode: str = "beauty"):
        """
        Initialize the display manager.

        Parameters
        ----------
        mode : str
            Display mode: 'json' or 'beauty'
        """
        self.mode = DisplayMode.BEAUTY if mode.lower() == "beauty" else DisplayMode.JSON
        self._display_enabled = True

    def set_mode(self, mode: str) -> None:
        """
        Set the display mode.

        Parameters
        ----------
        mode : str
            Display mode: 'json' or 'beauty'
        """
        self.mode = DisplayMode.BEAUTY if mode.lower() == "beauty" else DisplayMode.JSON

    def _print(self, text: str) -> None:
        """Print text if display is enabled."""
        if self._display_enabled:
            logger.info(text)

    def _print_json(self, data: dict) -> None:
        """Print data in JSON format."""
        self._print(json.dumps(data, indent=2, default=str))

    def _wrap_text(self, text: str, max_length: int = 60) -> str:
        """
        Wrap text to fit within max_length.

        Parameters
        ----------
        text : str
            Text to wrap
        max_length : int
            Maximum line length

        Returns
        -------
        str
            Wrapped text
        """
        if isinstance(text, dict):
            text = json.dumps(text, indent=2)

        words = text.split()
        wrapped = ""
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 > max_length:
                wrapped += current_line + "\n" if current_line else word
                current_line = word
            elif current_line:
                current_line += " " + word
            else:
                current_line = word

        if current_line:
            wrapped += current_line

        return wrapped

    def _print_symbol_header(self, symbol: str) -> None:
        self._print(f"\n{Fore.WHITE}{Style.BRIGHT}Analysis for {Fore.CYAN}{symbol}{Style.RESET_ALL}")
        self._print(f"{Fore.WHITE}{Style.BRIGHT}{'=' * 50}{Style.RESET_ALL}")

    def _format_agent_row(
        self,
        agent_name: str,
        signal_type: str,
        confidence: float,
        reasoning: str,
        color: str,
    ) -> list[str]:
        return [
            f"{color}{agent_name}{Style.RESET_ALL}" if color else f"{Fore.CYAN}{agent_name}{Style.RESET_ALL}",
            f"{color}{signal_type}{Style.RESET_ALL}",
            f"{Fore.WHITE}{confidence}%{Style.RESET_ALL}",
            f"{Fore.WHITE}{reasoning}{Style.RESET_ALL}",
        ]

    def _collect_analyst_rows(self, symbol: str, analyst_signals: dict) -> list[list[str]]:
        rows: list[list[str]] = []
        for agent, signals in analyst_signals.items():
            if symbol not in signals or agent == "crypto_risk_management_agent":
                continue
            signal = signals[symbol]
            agent_name = (
                agent.replace("crypto_technical", "Technical Analyst").replace("_agent", "").replace("_", " ").title()
            )
            signal_type = signal.get("signal", "").upper()
            confidence = signal.get("confidence", 0) * 100
            color_map = {
                "STRONG_BUY": Fore.GREEN,
                "BUY": Fore.GREEN,
                "HOLD": Fore.YELLOW,
                "SELL": Fore.RED,
                "STRONG_SELL": Fore.RED,
            }
            color = color_map.get(signal_type, Fore.WHITE)
            reasoning = signal.get("reasoning", "")
            reasoning_str = json.dumps(reasoning, indent=2) if isinstance(reasoning, dict) else str(reasoning)
            rows.append(
                self._format_agent_row(
                    agent_name,
                    signal_type,
                    confidence,
                    self._wrap_text(reasoning_str),
                    color,
                )
            )
        return rows

    def _collect_sentiment_rows(self, symbol: str, sentiment_signals: dict) -> list[list[str]]:
        rows: list[list[str]] = []
        for agent, signals in sentiment_signals.items():
            if symbol not in signals:
                continue
            signal = signals[symbol]
            agent_name = f"Sentiment ({agent.replace('_agent', '').replace('_', ' ').title()})"
            signal_type = signal.get("sentiment", "").upper()
            confidence = signal.get("confidence", 0) * 100
            color_map = {
                "VERY_POSITIVE": Fore.GREEN,
                "POSITIVE": Fore.GREEN,
                "NEUTRAL": Fore.YELLOW,
                "NEGATIVE": Fore.RED,
                "VERY_NEGATIVE": Fore.RED,
            }
            color = color_map.get(signal_type, Fore.WHITE)
            reasoning = signal.get("reasoning", "")
            reasoning_str = json.dumps(reasoning, indent=2) if isinstance(reasoning, dict) else str(reasoning)
            rows.append(
                self._format_agent_row(
                    agent_name,
                    signal_type,
                    confidence,
                    self._wrap_text(reasoning_str),
                    color,
                )
            )
        return rows

    def _collect_persona_rows(self, symbol: str, persona_signals: dict) -> list[list[str]]:
        rows: list[list[str]] = []
        for agent_data in persona_signals.values():
            agent_sigs = agent_data.get("agent_signals", {})
            for agent_key, signals in agent_sigs.items():
                if isinstance(signals, dict) and symbol in signals:
                    signal = signals[symbol]
                    agent_name = agent_key.replace("_", " ").title()
                    signal_type = signal.get("signal", "").upper()
                    confidence = signal.get("confidence", 0) * 100
                    color_map = {
                        "STRONG_BUY": Fore.GREEN,
                        "BUY": Fore.GREEN,
                        "HOLD": Fore.YELLOW,
                        "SELL": Fore.RED,
                        "STRONG_SELL": Fore.RED,
                    }
                    color = color_map.get(signal_type, Fore.WHITE)
                    reasoning = signal.get("reasoning", "")
                    rows.append(
                        [
                            f"{Fore.BLUE}{agent_name}{Style.RESET_ALL}",
                            f"{color}{signal_type}{Style.RESET_ALL}",
                            f"{Fore.WHITE}{confidence:.1f}%{Style.RESET_ALL}",
                            f"{Fore.WHITE}{self._wrap_text(reasoning[:200])}{Style.RESET_ALL}",
                        ]
                    )
                    break
        return rows

    def _print_agent_table(self, symbol: str, table_data: list[list[str]]) -> None:
        self._print(
            "\n"
            f"{Fore.WHITE}{Style.BRIGHT}AGENT ANALYSIS:{Style.RESET_ALL} "
            f"[{Fore.CYAN}{symbol}{Style.RESET_ALL}]"
        )
        if not table_data:
            self._print("No analyst data available")
            return
        self._print(
            tabulate(
                table_data,
                headers=[f"{Fore.WHITE}Agent", "Signal", "Confidence", "Reasoning"],
                tablefmt="grid",
                colalign=("left", "center", "right", "left"),
            )
        )

    def _print_decision_block(self, symbol: str, decision: dict) -> None:
        action = decision.get("action", "").upper()
        color = {"BUY": Fore.GREEN, "SELL": Fore.RED, "HOLD": Fore.YELLOW}.get(action, Fore.WHITE)
        reasoning = self._wrap_text(decision.get("reasoning", ""))
        confidence = decision.get("confidence")
        confidence_str = f"{confidence:.1f}%" if confidence is not None else "N/A"
        decision_data = [
            ["Action", f"{color}{action}{Style.RESET_ALL}"],
            ["Quantity", f"{color}{decision.get('quantity', 0)}{Style.RESET_ALL}"],
            ["Confidence", f"{Fore.WHITE}{confidence_str}{Style.RESET_ALL}"],
            ["Reasoning", f"{Fore.WHITE}{reasoning}{Style.RESET_ALL}"],
        ]
        self._print(
            "\n"
            f"{Fore.WHITE}{Style.BRIGHT}TRADING DECISION:{Style.RESET_ALL} "
            f"[{Fore.CYAN}{symbol}{Style.RESET_ALL}]"
        )
        self._print(tabulate(decision_data, tablefmt="grid", colalign=("left", "left")))

    def _print_portfolio_summary(self, decisions: dict, analyst_signals: dict) -> None:
        self._print(f"\n{Fore.WHITE}{Style.BRIGHT}PORTFOLIO SUMMARY:{Style.RESET_ALL}")
        portfolio_data: list[list[str]] = []
        for symbol, decision in decisions.items():
            action = decision.get("action", "").upper()
            action_color = {"BUY": Fore.GREEN, "SELL": Fore.RED, "HOLD": Fore.YELLOW}.get(action, Fore.WHITE)
            confidence = decision.get("confidence")
            confidence_str = f"{confidence:.1f}%" if confidence is not None else "N/A"
            bullish_count = bearish_count = neutral_count = 0
            for signals in analyst_signals.values():
                if symbol in signals:
                    signal_type = signals[symbol].get("signal", "").upper()
                    if signal_type in ["STRONG_BUY", "BUY"]:
                        bullish_count += 1
                    elif signal_type in ["STRONG_SELL", "SELL"]:
                        bearish_count += 1
                    elif signal_type == "HOLD":
                        neutral_count += 1
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
        self._print(tabulate(portfolio_data, headers=headers, tablefmt="grid"))

    def print_trading_output(self, result: dict) -> None:
        """
        Print formatted trading results.

        Parameters
        ----------
        result : dict
            Dictionary containing decisions and analyst signals
        """
        if self.mode == DisplayMode.JSON:
            self._print_json(result)
            return

        # Beauty mode (existing fancy display)
        decisions = result.get("decisions")
        if not decisions:
            self._print(f"{Fore.RED}No trading decisions available{Style.RESET_ALL}")
            return

        analyst_signals = result.get("analyst_signals", {})
        sentiment_signals = result.get("sentiment_signals", {})
        persona_signals = result.get("persona_signals", {})

        for symbol, decision in decisions.items():
            self._print_symbol_header(symbol)
            table_data: list[list[str]] = []
            table_data.extend(self._collect_analyst_rows(symbol, analyst_signals))
            table_data.extend(self._collect_sentiment_rows(symbol, sentiment_signals))
            table_data.extend(self._collect_persona_rows(symbol, persona_signals))
            self._print_agent_table(symbol, table_data)
            self._print_decision_block(symbol, decision)

        self._print_portfolio_summary(decisions, analyst_signals)

    def print_backtest_results(self, table_rows: list) -> None:
        """
        Print backtest results.

        Parameters
        ----------
        table_rows : list
            List of table row data
        """
        if self.mode == DisplayMode.JSON:
            self._print_json({"rows": table_rows})
            return

        # Beauty mode
        clear_cmd = "cls" if os.name == "nt" else "clear"
        subprocess.run([clear_cmd], check=False)  # noqa: S603

        ticker_rows = []
        summary_rows = []

        for row in table_rows:
            if isinstance(row[1], str) and "PORTFOLIO SUMMARY" in row[1]:
                summary_rows.append(row)
            else:
                ticker_rows.append(row)

        if summary_rows:
            latest_summary = max(summary_rows, key=lambda r: r[0])
            self._print(f"\n{Fore.WHITE}{Style.BRIGHT}PORTFOLIO SUMMARY:{Style.RESET_ALL}")

            # Extract values from colored strings
            position_str = latest_summary[7].split("$")[1].split(Style.RESET_ALL)[0].replace(",", "")
            cash_str = latest_summary[8].split("$")[1].split(Style.RESET_ALL)[0].replace(",", "")
            total_str = latest_summary[9].split("$")[1].split(Style.RESET_ALL)[0].replace(",", "")

            self._print(f"Cash Balance: {Fore.CYAN}${float(cash_str):,.2f}{Style.RESET_ALL}")
            self._print(f"Total Position Value: {Fore.YELLOW}${float(position_str):,.2f}{Style.RESET_ALL}")
            self._print(f"Total Value: {Fore.WHITE}${float(total_str):,.2f}{Style.RESET_ALL}")

            if len(latest_summary) > 10:
                self._print(f"Portfolio Return: {latest_summary[10]}")
            if len(latest_summary) > 14 and latest_summary[14]:
                self._print(f"Benchmark Return: {latest_summary[14]}")

        self._print("\n" * 2)

        self._print(
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
                    "left",
                    "left",
                    "center",
                    "right",
                    "right",
                    "right",
                    "right",
                    "right",
                ),
            )
        )

        self._print("\n" * 4)

    def format_backtest_row(
        self,
        date: str,
        ticker: str,
        action: str,
        quantity: float,
        price: float,
        long_shares: float = 0,
        short_shares: float = 0,
        position_value: float = 0,
        **kwargs,
    ) -> list:
        """
        Format a backtest row.

        Parameters
        ----------
        date : str
            Date string
        ticker : str
            Ticker symbol
        action : str
            Trading action
        quantity : float
            Quantity
        price : float
            Price
        long_shares : float
            Long shares
        short_shares : float
            Short shares
        position_value : float
            Position value
        **kwargs
            Additional arguments

        Returns
        -------
        list
            Formatted row
        """
        if self.mode == DisplayMode.JSON:
            return [date, ticker, action, quantity, price, long_shares, short_shares, position_value]

        # Beauty mode - existing formatting logic
        action_color = {
            "BUY": Fore.GREEN,
            "COVER": Fore.GREEN,
            "SELL": Fore.RED,
            "SHORT": Fore.RED,
            "HOLD": Fore.WHITE,
        }.get(action.upper(), Fore.WHITE)

        if kwargs.get("is_summary"):
            return_pct = kwargs.get("return_pct", 0)
            return_color = Fore.GREEN if return_pct >= 0 else Fore.RED
            benchmark_return_pct = kwargs.get("benchmark_return_pct")
            benchmark_str = ""
            if benchmark_return_pct is not None:
                bench_color = Fore.GREEN if benchmark_return_pct >= 0 else Fore.RED
                benchmark_str = f"{bench_color}{benchmark_return_pct:+.2f}%{Style.RESET_ALL}"

            return [
                date,
                f"{Fore.WHITE}{Style.BRIGHT}PORTFOLIO SUMMARY{Style.RESET_ALL}",
                "",
                "",
                "",
                "",
                "",
                f"{Fore.YELLOW}${kwargs.get('total_position_value', 0):,.2f}{Style.RESET_ALL}",
                f"{Fore.CYAN}${kwargs.get('cash_balance', 0):,.2f}{Style.RESET_ALL}",
                f"{Fore.WHITE}${kwargs.get('total_value', 0):,.2f}{Style.RESET_ALL}",
                f"{return_color}{return_pct:+.2f}%{Style.RESET_ALL}",
                f"{Fore.YELLOW}{kwargs.get('sharpe_ratio', 0):.2f}{Style.RESET_ALL}"
                if kwargs.get("sharpe_ratio") is not None
                else "",
                f"{Fore.YELLOW}{kwargs.get('sortino_ratio', 0):.2f}{Style.RESET_ALL}"
                if kwargs.get("sortino_ratio") is not None
                else "",
                f"{Fore.RED}{kwargs.get('max_drawdown', 0):.2f}%{Style.RESET_ALL}"
                if kwargs.get("max_drawdown") is not None
                else "",
                benchmark_str,
            ]

        return [
            date,
            f"{Fore.CYAN}{ticker}{Style.RESET_ALL}",
            f"{action_color}{action.upper()}{Style.RESET_ALL}",
            f"{action_color}{quantity:,.0f}{Style.RESET_ALL}",
            f"{Fore.WHITE}{price:,.2f}{Style.RESET_ALL}",
            f"{Fore.GREEN}{long_shares:,.0f}{Style.RESET_ALL}",
            f"{Fore.RED}{short_shares:,.0f}{Style.RESET_ALL}",
            f"{Fore.YELLOW}{position_value:,.2f}{Style.RESET_ALL}",
        ]


# Global instance
_display_manager = DisplayManager()


def get_display_manager() -> DisplayManager:
    """
    Get the global display manager instance.

    Returns
    -------
    DisplayManager
        Display manager instance
    """
    return _display_manager


def set_display_mode(mode: str) -> None:
    """
    Set the global display mode.

    Parameters
    ----------
    mode : str
        Display mode: 'json' or 'beauty'
    """
    _display_manager.set_mode(mode)


def print_trading_output(result: dict) -> None:
    """
    Print trading output using the current display mode.

    Parameters
    ----------
    result : dict
        Trading results dictionary
    """
    _display_manager.print_trading_output(result)


def print_backtest_results(table_rows: list) -> None:
    """
    Print backtest results using the current display mode.

    Parameters
    ----------
    table_rows : list
        Backtest table rows
    """
    _display_manager.print_backtest_results(table_rows)


def format_backtest_row(**kwargs) -> list:
    """
    Format a backtest row using the current display mode.

    Returns
    -------
    list
        Formatted row data
    """
    return _display_manager.format_backtest_row(**kwargs)
