import sys
from datetime import datetime, timedelta

import click
import structlog
from app.backend.src.backtesting.engine import BacktestEngine
from app.backend.src.backtesting.types import PerformanceMetrics
from app.backend.src.main import run_crypto_hedge_fund
from app.backend.src.utils.display_manager import set_display_mode
from colorama import Fore, Style

logger = structlog.get_logger(__name__)


def run_backtest(backtester: BacktestEngine) -> PerformanceMetrics | None:
    """Run the backtest with graceful KeyboardInterrupt handling."""
    try:
        performance_metrics = backtester.run_backtest()
        logger.info("\n%sBacktest completed successfully!%s", Fore.GREEN, Style.RESET_ALL)
        return performance_metrics
    except KeyboardInterrupt:
        logger.info("\n\n%sBacktest interrupted by user.%s", Fore.YELLOW, Style.RESET_ALL)

        # Try to show any partial results that were computed
        try:
            portfolio_values = backtester.get_portfolio_values()
            if len(portfolio_values) > 1:
                logger.info("%sPartial results available.%s", Fore.GREEN, Style.RESET_ALL)

                # Show basic summary from the available portfolio values
                first_value = portfolio_values[0]["Portfolio Value"]
                last_value = portfolio_values[-1]["Portfolio Value"]
                total_return = ((last_value - first_value) / first_value) * 100

                logger.info("%sInitial Portfolio Value: $%s%s", Fore.CYAN, f"{first_value:,.2f}", Style.RESET_ALL)
                logger.info("%sFinal Portfolio Value: $%s%s", Fore.CYAN, f"{last_value:,.2f}", Style.RESET_ALL)
                logger.info("%sTotal Return: %s%%%s", Fore.CYAN, f"{total_return:+.2f}", Style.RESET_ALL)
        except Exception as e:
            logger.info("%sCould not generate partial results: %s%s", Fore.RED, str(e), Style.RESET_ALL)

        sys.exit(0)


@click.command()
@click.option("--tickers", required=True, help="Comma-separated list of crypto symbols")
@click.option("--start-date", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--end-date", default=None, help="End date (YYYY-MM-DD)")
@click.option("--initial-cash", default=100000.0, help="Initial cash amount")
@click.option("--model", default="openai/gpt-4o-mini", help="LLM model to use")
@click.option(
    "--model-provider",
    "model_provider",
    default="OpenRouter",
    type=click.Choice(
        ["OpenAI", "Anthropic", "Groq", "DeepSeek", "Google", "OpenRouter", "LiteLLM"], case_sensitive=False
    ),
    help="LLM provider to use",
)
@click.option(
    "--display-mode",
    default="beauty",
    type=click.Choice(["json", "beauty"], case_sensitive=False),
    help="Output display mode: 'json' for structured output, 'beauty' for fancy colored tables",
)
def main(tickers, start_date, end_date, initial_cash, model, model_provider, display_mode):
    """Run crypto backtesting simulation."""
    # Set display mode
    set_display_mode(display_mode)

    # Parse tickers
    ticker_list = [t.strip().upper() for t in tickers.split(",")]

    # Parse dates
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    # Create and run the backtester
    backtester = BacktestEngine(
        agent=run_crypto_hedge_fund,
        tickers=ticker_list,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_cash,
        model_name=model,
        model_provider=model_provider,
        selected_analysts=None,  # Use all analysts by default
        initial_margin_requirement=0.1,  # Default margin requirement
    )

    # Run the backtest with graceful exit handling
    run_backtest(backtester)


if __name__ == "__main__":
    main()
