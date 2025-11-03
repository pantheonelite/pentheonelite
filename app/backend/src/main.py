"""Main CLI entry point for crypto hedge fund trading system."""

from datetime import datetime, timedelta
from pathlib import Path

import click
import structlog
from app.backend.src.agents.crypto_agent import CryptoAgent
from app.backend.src.utils.display_manager import print_trading_output, set_display_mode
from app.backend.src.utils.progress import AgentProgress
from dotenv import load_dotenv

logger = structlog.get_logger(__name__)

# Load environment variables
env_paths = [
    Path("app/backend/.env"),
    Path(".env"),
    Path(__file__).parent.parent / ".env",
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break
else:
    load_dotenv()


def run_crypto_hedge_fund(
    symbols: list[str],
    start_date: str,
    end_date: str,
    portfolio: dict,
    *,
    show_reasoning: bool = False,
    model_name: str = "gpt-4o-mini",
    model_provider: str = "OpenRouter",
) -> dict:
    """Run crypto hedge fund analysis and return trading decisions."""
    progress_tracker = AgentProgress()
    progress_tracker.start()

    try:
        # Update progress for workflow initialization
        progress_tracker.update_status("workflow_init", None, "Initializing crypto trading agent...")

        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=None)  # noqa: DTZ007
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=None)  # noqa: DTZ007

        # Create crypto agent
        agent = CryptoAgent(model_name=model_name, model_provider=model_provider, show_agent_graph=False)

        progress_tracker.update_status("workflow_init", None, "Running crypto trading agent...")

        # Run agent
        results = agent.run(
            tickers=symbols,
            end_date=end_dt,
            portfolio=portfolio,
            start_date=start_dt,
            _show_reasoning=show_reasoning,
        )

        progress_tracker.update_status("workflow_init", None, "Agent completed successfully")

        return {
            "decisions": results.get("decisions", {}),
            "portfolio_allocations": results.get("portfolio_allocations", {}),
            "analyst_signals": results.get("analyst_signals", {}),
            "technical_signals": results.get("analyst_signals", {}),  # Keep for backwards compatibility
            "sentiment_signals": results.get("sentiment_signals", {}),
            "persona_signals": results.get("persona_signals", {}),
            "risk_assessments": results.get("risk_signals", {}),
            "price_data": results.get("price_data", {}),
            "execution_timestamp": results.get("execution_timestamp"),
            "progress_percentage": 100.0,
            "error_messages": [],
        }
    finally:
        progress_tracker.stop()


@click.command()
@click.option("--symbols", required=True, help="Comma-separated list of crypto symbols")
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
@click.option("--start-date", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--end-date", default=None, help="End date (YYYY-MM-DD)")
@click.option("--initial-cash", default=100000.0, help="Initial cash amount")
@click.option("--show-reasoning", is_flag=True, help="Show agent reasoning")
@click.option(
    "--display-mode",
    default="beauty",
    type=click.Choice(["json", "beauty"], case_sensitive=False),
    help="Output display mode: 'json' for structured output, 'beauty' for fancy colored tables",
)
def main(symbols, model, model_provider, start_date, end_date, initial_cash, show_reasoning, display_mode):
    """Run crypto hedge fund trading system."""
    # Set display mode
    set_display_mode(display_mode)

    # Parse symbols
    symbol_list = [s.strip().upper() for s in symbols.split(",")]

    # Parse dates
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    # Create portfolio
    portfolio = {
        "cash": initial_cash,
        "positions": {
            symbol: {"long": 0.0, "short": 0.0, "long_cost_basis": 0.0, "short_cost_basis": 0.0}
            for symbol in symbol_list
        },
        "realized_gains": dict.fromkeys(symbol_list, 0.0),
    }

    # Run hedge fund
    result = run_crypto_hedge_fund(
        symbols=symbol_list,
        start_date=start_date,
        end_date=end_date,
        portfolio=portfolio,
        show_reasoning=show_reasoning,
        model_name=model,
        model_provider=model_provider,
    )

    # Print results using display manager
    print_trading_output(result)


if __name__ == "__main__":
    main()
