import argparse
from datetime import datetime

import questionary
import structlog
from app.backend.src.cli.input import LLM_ORDER, get_model_info
from app.backend.src.utils.analysts import get_crypto_analyst_nodes
from colorama import Fore, Style, init
from dateutil.relativedelta import relativedelta

from .engine import BacktestEngine

logger = structlog.get_logger(__name__)


def main() -> int:
    """Main entry point for the crypto backtesting CLI."""
    parser = argparse.ArgumentParser(description="Run crypto backtesting engine (modular)")
    parser.add_argument("--symbols", type=str, required=False, help="Comma-separated crypto symbols (e.g., BTC,ETH)")
    parser.add_argument(
        "--end-date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="End date YYYY-MM-DD",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=(datetime.now() - relativedelta(months=1)).strftime("%Y-%m-%d"),
        help="Start date YYYY-MM-DD",
    )
    parser.add_argument("--initial-capital", type=float, default=100000)
    parser.add_argument("--margin-requirement", type=float, default=0.0)
    parser.add_argument("--analysts", type=str, required=False)
    parser.add_argument("--analysts-all", action="store_true")

    args = parser.parse_args()
    init(autoreset=True)

    symbols = [s.strip() for s in args.symbols.split(",")] if args.symbols else []

    # Get crypto analyst nodes
    analyst_nodes = get_crypto_analyst_nodes()
    analyst_order = [(display, key) for key, (display, _) in analyst_nodes.items()]

    # Analysts selection is simplified; no interactive prompts here
    if args.analysts_all:
        selected_analysts = [a[1] for a in analyst_order]
    elif args.analysts:
        selected_analysts = [a.strip() for a in args.analysts.split(",") if a.strip()]
    else:
        # Interactive analyst selection (same as legacy backtester)
        choices = questionary.checkbox(
            "Use the Space bar to select/unselect crypto analysts.",
            choices=[questionary.Choice(display, value=value) for display, value in analyst_order],
            instruction="\n\nPress 'a' to toggle all.\n\nPress Enter when done to run the crypto hedge fund.",
            validate=lambda x: len(x) > 0 or "You must select at least one analyst.",
            style=questionary.Style(
                [
                    ("checkbox-selected", "fg:green"),
                    ("selected", "fg:green noinherit"),
                    ("highlighted", "noinherit"),
                    ("pointer", "noinherit"),
                ]
            ),
        ).ask()
        if not choices:
            logger.info("\n\nInterrupt received. Exiting...")
            return 1
        selected_analysts = choices
        analyst_names = ", ".join(
            Fore.GREEN + choice.title().replace("_", " ") + Style.RESET_ALL for choice in choices
        )
        logger.info("\nSelected crypto analysts: %s\n", analyst_names)

    # Model selection simplified: default to first ordered model
    model_choice = questionary.select(
        "Select your LLM model:",
        choices=[questionary.Choice(display, value=(name, provider)) for display, name, provider in LLM_ORDER],
        style=questionary.Style(
            [
                ("selected", "fg:green bold"),
                ("pointer", "fg:green bold"),
                ("highlighted", "fg:green"),
                ("answer", "fg:green bold"),
            ]
        ),
    ).ask()
    if not model_choice:
        logger.info("\n\nInterrupt received. Exiting...")
        return 1
    model_name, model_provider = model_choice
    model_info = get_model_info(model_name, model_provider)
    if model_info and model_info.get("is_custom", False):
        model_name = questionary.text("Enter the custom model name:").ask()
        if not model_name:
            logger.info("\n\nInterrupt received. Exiting...")
            return 1
    logger.info(
        "\nSelected %s%s%s model: %s%s%s\n",
        Fore.CYAN,
        model_provider,
        Style.RESET_ALL,
        Fore.GREEN + Style.BRIGHT,
        model_name,
        Style.RESET_ALL,
    )

    engine = BacktestEngine(
        symbols=symbols,
        start_date=args.start_date,
        end_date=args.end_date,
        initial_capital=args.initial_capital,
        model_name=model_name,
        model_provider=model_provider,
        selected_analysts=selected_analysts,
        initial_margin_requirement=args.margin_requirement,
    )

    metrics = engine.run_backtest()
    values = engine.get_portfolio_values()

    # Minimal terminal output (no plots)
    if values:
        logger.info("\n%s%sENGINE RUN COMPLETE%s", Fore.WHITE, Style.BRIGHT, Style.RESET_ALL)
        last_value = values[-1]["Portfolio Value"]
        start_value = values[0]["Portfolio Value"]
        total_return = (last_value / start_value - 1.0) * 100.0 if start_value else 0.0
        color = Fore.GREEN if total_return >= 0 else Fore.RED
        logger.info("Total Return: %s%.2f%%%s", color, total_return, Style.RESET_ALL)
    if metrics.get("sharpe_ratio") is not None:
        logger.info("Sharpe: %.2f", metrics["sharpe_ratio"])
    if metrics.get("sortino_ratio") is not None:
        logger.info("Sortino: %.2f", metrics["sortino_ratio"])
    if metrics.get("max_drawdown") is not None:
        md = abs(metrics["max_drawdown"]) if metrics["max_drawdown"] is not None else 0.0
        if metrics.get("max_drawdown_date"):
            logger.info("Max DD: %.2f%% on %s", md, metrics["max_drawdown_date"])
        else:
            logger.info("Max DD: %.2f%%", md)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
