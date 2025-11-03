import argparse
import sys
from dataclasses import dataclass
from datetime import datetime

import questionary
import structlog
from colorama import Fore, Style
from dateutil.relativedelta import relativedelta

from app.backend.src.llm.base_client import ModelProvider
from app.backend.src.utils.analysts import get_crypto_analyst_nodes

logger = structlog.get_logger(__name__)

# Mock the missing imports for now - format: [(display_name, model_name, provider), ...]
LLM_ORDER: list[tuple[str, str, str]] = [
    ("GPT-4 (OpenAI)", "gpt-4", "openai"),
    ("GPT-3.5 Turbo (OpenAI)", "gpt-3.5-turbo", "openai"),
]


def find_model_by_name(model_name: str):
    """Mock function for finding model by name."""
    return model_name


def get_model_info(model_name: str, provider: ModelProvider):
    """Mock function for getting model info."""
    return {"name": model_name, "provider": provider}


def get_crypto_agents_list():
    """Mock function for getting crypto agents list."""
    analyst_nodes = get_crypto_analyst_nodes()
    return [{"key": key, "name": name} for key, (name, _) in analyst_nodes.items()]


def add_common_args(
    parser: argparse.ArgumentParser,
    *,
    require_symbols: bool = False,
    include_analyst_flags: bool = True,
    _include_ollama: bool = True,
) -> argparse.ArgumentParser:
    """Add common command line arguments to the parser."""
    parser.add_argument(
        "--symbols",
        type=str,
        required=require_symbols,
        help="Comma-separated list of crypto symbols (e.g., BTC/USDT,ETH/USDT,BNB/USDT)",
    )
    if include_analyst_flags:
        parser.add_argument(
            "--analysts",
            type=str,
            required=False,
            help="Comma-separated list of analysts to use (e.g., crypto_analyst)",
        )
        parser.add_argument(
            "--analysts-all",
            action="store_true",
            help="Use all available analysts (overrides --analysts)",
        )
    parser.add_argument(
        "--model", type=str, required=False, help="Model name to use (e.g., gpt-4o)"
    )
    return parser


def add_date_args(
    parser: argparse.ArgumentParser, *, default_months_back: int | None = None
) -> argparse.ArgumentParser:
    """Add date-related command line arguments to the parser."""
    if default_months_back is None:
        parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
        parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    else:
        parser.add_argument(
            "--end-date",
            type=str,
            default=datetime.now().strftime("%Y-%m-%d"),
            help="End date in YYYY-MM-DD format",
        )
        parser.add_argument(
            "--start-date",
            type=str,
            default=(
                datetime.now() - relativedelta(months=default_months_back)
            ).strftime("%Y-%m-%d"),
            help="Start date in YYYY-MM-DD format",
        )
    return parser


def parse_symbols(symbols_arg: str | None) -> list[str]:
    """Parse comma-separated symbols string into a list."""
    if not symbols_arg:
        return []
    return [symbol.strip() for symbol in symbols_arg.split(",") if symbol.strip()]


def select_analysts(flags: dict | None = None) -> list[str]:
    """Select crypto analysts interactively."""
    crypto_agents = get_crypto_agents_list()
    crypto_analyst_order = [(agent["name"], agent["key"]) for agent in crypto_agents]

    if flags and flags.get("analysts_all"):
        return [a[1] for a in crypto_analyst_order]

    if flags and flags.get("analysts"):
        return [a.strip() for a in flags["analysts"].split(",") if a.strip()]

    choices = questionary.checkbox(
        "Select your AI crypto analysts.",
        choices=[
            questionary.Choice(display, value=value)
            for display, value in crypto_analyst_order
        ],
        instruction=(
            "\n\nInstructions: \n1. Press Space to select/unselect analysts.\n"
            "2. Press 'a' to select/unselect all.\n3. Press Enter when done."
        ),
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
        sys.exit(0)

    analyst_names = ", ".join(
        Fore.GREEN + c.title().replace("_", " ") + Style.RESET_ALL for c in choices
    )
    logger.info("\nSelected analysts: %s\n", analyst_names, analysts=choices)
    return choices


def select_model(
    *, _use_ollama: bool, model_flag: str | None = None
) -> tuple[str, str]:
    """Select a model interactively."""
    model_name: str = ""
    model_provider: str | None = None

    if model_flag:
        model = find_model_by_name(model_flag)
        if model:
            logger.info(
                "\nUsing specified model: %s%s%s - %s%s%s\n",
                Fore.CYAN,
                model.provider.value,
                Style.RESET_ALL,
                Fore.GREEN + Style.BRIGHT,
                model.model_name,
                Style.RESET_ALL,
                provider=model.provider.value,
                model_name=model.model_name,
            )
            return model.model_name, model.provider.value
        logger.info(
            "%sModel '%s' not found. Please select a model.%s",
            Fore.RED,
            model_flag,
            Style.RESET_ALL,
            model_flag=model_flag,
        )

    model_choice = questionary.select(
        "Select your LLM model:",
        choices=[
            questionary.Choice(display, value=(name, provider))
            for display, name, provider in LLM_ORDER
        ],
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
        sys.exit(0)

    model_name, model_provider = model_choice

    model_info = get_model_info(model_name, model_provider)
    if model_info and model_info.get("is_custom", False):
        model_name = questionary.text("Enter the custom model name:").ask()
        if not model_name:
            logger.info("\n\nInterrupt received. Exiting...")
            sys.exit(0)

    if model_info:
        logger.info(
            "\nSelected %s%s%s model: %s%s%s\n",
            Fore.CYAN,
            model_provider,
            Style.RESET_ALL,
            Fore.GREEN + Style.BRIGHT,
            model_name,
            Style.RESET_ALL,
            provider=model_provider,
            model_name=model_name,
        )
    else:
        model_provider = "Unknown"
        logger.info(
            "\nSelected model: %s%s%s\n",
            Fore.GREEN + Style.BRIGHT,
            model_name,
            Style.RESET_ALL,
            provider=model_provider,
            model_name=model_name,
        )

    return model_name, model_provider or ""


def resolve_dates(
    start_date: str | None,
    end_date: str | None,
    *,
    default_months_back: int | None = None,
) -> tuple[str, str]:
    """Resolve start and end dates with validation and defaults."""
    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=None)  # noqa: DTZ007
        except ValueError:
            raise ValueError("Start date must be in YYYY-MM-DD format") from None
    if end_date:
        try:
            datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=None)  # noqa: DTZ007
        except ValueError:
            raise ValueError("End date must be in YYYY-MM-DD format") from None

    final_end = end_date or datetime.now().strftime("%Y-%m-%d")
    if start_date:
        final_start = start_date
    else:
        months = default_months_back if default_months_back is not None else 3
        end_date_obj = datetime.strptime(final_end, "%Y-%m-%d").replace(tzinfo=None)  # noqa: DTZ007
        final_start = (end_date_obj - relativedelta(months=months)).strftime("%Y-%m-%d")
    return final_start, final_end


@dataclass
class CLIInputs:
    """Command line interface inputs structure."""

    symbols: list[str]
    selected_analysts: list[str]
    model_name: str
    model_provider: str
    start_date: str
    end_date: str
    initial_cash: float
    show_reasoning: bool = False
    show_agent_graph: bool = False
    raw_args: argparse.Namespace | None = None


def parse_cli_inputs(
    *,
    description: str,
    require_symbols: bool,
    default_months_back: int | None,
    include_graph_flag: bool = False,
    include_reasoning_flag: bool = False,
) -> CLIInputs:
    """Parse command line inputs and return structured data."""
    parser = argparse.ArgumentParser(description=description)

    # Common/interactive flags
    add_common_args(
        parser,
        require_symbols=require_symbols,
        include_analyst_flags=True,
        _include_ollama=False,
    )
    add_date_args(parser, default_months_back=default_months_back)

    # Funding flags (standardized, with alias)
    parser.add_argument(
        "--initial-cash",
        "--initial-capital",
        dest="initial_cash",
        type=float,
        default=100000.0,
        help="Initial cash position (alias: --initial-capital). Defaults to 100000.0",
    )

    if include_reasoning_flag:
        parser.add_argument(
            "--show-reasoning",
            action="store_true",
            help="Show reasoning from each agent",
        )
    if include_graph_flag:
        parser.add_argument(
            "--show-agent-graph", action="store_true", help="Show the agent graph"
        )

    args = parser.parse_args()

    # Normalize parsed values
    symbols = parse_symbols(getattr(args, "symbols", None))
    selected_analysts = select_analysts(
        {
            "analysts_all": getattr(args, "analysts_all", False),
            "analysts": getattr(args, "analysts", None),
        }
    )
    model_name = getattr(args, "model", "gpt-4.1-mini")
    model_provider = getattr(args, "model_provider", "OpenRouter")

    start_date, end_date = resolve_dates(
        getattr(args, "start_date", None),
        getattr(args, "end_date", None),
        default_months_back=default_months_back,
    )

    return CLIInputs(
        symbols=symbols,
        selected_analysts=selected_analysts,
        model_name=model_name,
        model_provider=model_provider,
        start_date=start_date,
        end_date=end_date,
        initial_cash=getattr(args, "initial_cash", 100000.0),
        show_reasoning=getattr(args, "show_reasoning", False),
        show_agent_graph=getattr(args, "show_agent_graph", False),
        raw_args=args,
    )
