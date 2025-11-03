# Repository Guidelines

## Project Structure & Module Organization

- `src/` houses the trading graph, agent logic (`agents/`, `graph/`, `tools/`), and CLI entry points (`main.py`, `backtester.py`).
- `app/backend/` contains the FastAPI service; route definitions live in `routes/`, orchestration in `services/`, and database artifacts under `database/` and `alembic/`. **Alembic migration files should follow the `000x_description.py` naming convention (e.g., `0001_initial_schema.py`).**
- `app/frontend/` is the Vite + React dashboard (Tailwind config in `tailwind.config.ts`, static assets in `public/`).
- `tests/` mirrors the Python domains with fixtures in `tests/fixtures/` and scenario suites under `tests/backtesting/integration/`.
- `docker/` packages runtime images for local or CI builds.

### API Schemas Convention
- Keep all FastAPI/Pydantic request/response models under `app/backend/api/schemas/`.
- Do not declare `__all__` in leaf schema modules. Export symbols centrally from `app/backend/api/schemas/__init__.py` only.
- Routers must not define inline Pydantic models. Import from `app.backend.api.schemas`.
- Group related models by domain (e.g., `council_view_schemas.py`, `websocket_schemas.py`, `storage_schemas.py`).

### Module Export Convention

- **`__all__` usage**: Only use `__all__` in `__init__.py` files, never in regular module files.
- **Direct imports in `__init__.py`**: Import symbols directly in `__init__.py` without creating intermediate lists or list comprehensions.
- **Example Pattern**:

  ```python
  # ❌ BAD: Using __all__ in regular module
  # my_module.py
  __all__ = ["function_a", "function_b"]

  # ❌ BAD: Creating lists in __init__.py
  # __init__.py
  from .module1 import tool1, tool2
  from .module2 import tool3, tool4
  tools = [tool1, tool2, tool3, tool4]
  __all__ = ["tools"]

  # ✅ GOOD: Direct imports in __init__.py only
  # __init__.py
  from .module1 import tool1, tool2
  from .module2 import tool3, tool4

  __all__ = ["tool1", "tool2", "tool3", "tool4"]
  ```

## Build, Test, and Development Commands

**`uv` is the designated Python package manager for this project.**

- `uv sync --all-groups` sets up the Python toolchain; run from the repo root.
- `uv run python src/main.py --ticker BTCUSDT,ETHUSDT --start-date 2024-01-01` executes the multi-agent CLI with crypto pairs.
- `uv run python src/backtester.py --ticker BTCUSDT,ETHUSDT` replays historical crypto trades.
- `uv run uvicorn main:app --reload --app-dir app/backend` runs the API for the web app.
- `cd app/frontend && pnpm install && pnpm dev` starts the Vite dev server.
- `uv run pytest` runs all Python tests; use `-k` to target a subset.
- `uv run pytest tests/test_aster_services.py` runs Aster-specific tests.
- `uv run python -m app.backend.src.tools.aster.test_connection` tests Aster API connectivity.

## Service Architecture & Object-Oriented Programming

### Service Layer Design
- **OOP Pattern:** All services in `app/backend/services/` follow Object-Oriented Programming patterns with proper class-based architecture.
- **Service Classes:** Each service is implemented as a class with methods for specific functionality:
  - `AgentService`: Manages agent function creation and registration
  - `GraphService`: Handles trading agent graph creation and execution
  - `PortfolioService`: Manages portfolio structures and calculations
  - `OllamaService`: Provides local LLM interaction capabilities
  - `CryptoBacktestService`: Executes cryptocurrency trading backtests
  - `BacktestService`: Core backtesting functionality
  - `ApiKeyService`: Manages API key operations

### Service Usage Pattern
```python
# Instantiate service classes directly
from app.backend.services.agent_service import AgentService
from app.backend.services.graph_service import GraphService
from app.backend.services.portfolio_service import PortfolioService

# Create service instances
agent_service = AgentService()
graph_service = GraphService()
portfolio_service = PortfolioService()

# Use service methods
agent_function = agent_service.create_agent_function(my_func, "agent_id")
graph = graph_service.create_graph(nodes, edges)
portfolio = portfolio_service.create_portfolio(10000, 0.1, ["BTC", "ETH"])

# Async methods use 'a' prefix
result = await graph_service.arun_graph(graph, portfolio, tickers, start_date, end_date, model_name, model_provider)
backtest_result = await backtest_service.arun_backtest(progress_callback=callback)
```

### Service Dependencies
- Services can depend on other services through composition
- `GraphService` uses `AgentService` internally for agent function creation
- Services maintain their own state and can be instantiated multiple times if needed

## Crypto Data & LangGraph Tools Integration

### Aster Finance API Integration
- **Installation:** `uv add git+https://github.com/asterdex/aster-connector-python.git` for Aster Finance API access
- **API Endpoints:**
  - Spot API: `https://api.aster.finance` - Spot trading and market data
  - Futures API: `https://fapi.aster.finance` - Futures trading and derivatives
  - WebSocket: `wss://stream.aster.finance` - Real-time data streaming
- **Authentication:** API key + secret key with HMAC SHA256 signature
- **Free Data:** Aster provides public market data (prices, volumes, order books) without API keys
- **Location:** Place Aster-based tools in `app/backend/src/tools/aster/` directory

### Aster Service Architecture
- **AsterMarketDataService:** Real-time price feeds, klines, order book data
- **AsterTradingService:** Order placement, execution, portfolio management
- **AsterWebSocketService:** Real-time data streaming and event handling
- **AsterRiskService:** Position sizing, risk management, margin calculations

### Aster API Integration Patterns
```python
# Service instantiation pattern
from app.backend.services.aster_service import AsterMarketDataService

# Create service with local configuration
config = AsterConfig(
    api_key="your_api_key",
    secret_key="your_secret_key",
    base_url="https://api.aster.finance"
)
aster_service = AsterMarketDataService(config)

# Async method usage with 'a' prefix
market_data = await aster_service.afetch_klines("BTCUSDT", "1h", 100)
order_book = await aster_service.afetch_order_book("BTCUSDT", 20)
```

### Aster Error Handling
- **RateLimitError:** Handle with exponential backoff (60s, 120s, 240s)
- **AuthenticationError:** Log and retry with fresh credentials
- **NetworkError:** Implement retry logic with circuit breaker pattern
- **OrderError:** Handle insufficient balance, invalid symbols, etc.

### Aster WebSocket Integration
```python
# WebSocket service pattern
class AsterWebSocketService:
    def __init__(self, config: AsterConfig):
        self.config = config
        self.websocket = None

    async def aconnect(self):
        """Connect to Aster WebSocket stream."""
        pass

    async def asubscribe_ticker(self, symbol: str):
        """Subscribe to real-time ticker updates."""
        pass

    async def asubscribe_depth(self, symbol: str):
        """Subscribe to order book depth updates."""
        pass
```

### LangGraph Custom Tools
- **Tool Development:** Create custom LangGraph tools for crypto data, news crawling, and web search
- **News Crawling:** Implement RSS feed readers and web scrapers for crypto sentiment analysis
- **Web Search:** Integrate search engines for real-time crypto information gathering
- **Location:** Place custom tools in `src/tools/` directory with clear naming conventions

### Aster Tool Integration Guidelines
- **Error Handling:** Implement robust error handling for API rate limits and network issues
- **Caching:** Use Redis for caching frequently accessed crypto data and news content
- **Async Operations:** Leverage `asyncio` for concurrent data fetching from multiple sources
- **Testing:** Create comprehensive tests for crypto data tools and news crawling functionality
- **Rate Limiting:** Implement client-side rate limiting with exponential backoff
- **WebSocket Management:** Handle connection drops and automatic reconnection
- **Order Management:** Implement proper order state tracking and error handling
- **Position Tracking:** Real-time position monitoring with PnL calculations

### Aster Database Schema
- **aster_api_keys:** Store API credentials with encryption
- **aster_trades:** Trade execution records with timestamps
- **aster_positions:** Position tracking with real-time updates
- **aster_market_data:** Cached market data with TTL
- **aster_orders:** Order history and status tracking
- **aster_accounts:** Account balance and margin information

### Aster Configuration Management
```python
# config/aster.py
from pydantic import BaseSettings

class AsterConfig(BaseSettings):
    api_key: str
    secret_key: str
    base_url: str = "https://api.aster.finance"
    futures_url: str = "https://fapi.aster.finance"
    websocket_url: str = "wss://stream.aster.finance"
    rate_limit_per_minute: int = 1200
    max_retries: int = 3
    retry_delay: int = 1

    class Config:
        env_file = ".env"
```

### Aster Testing Patterns
```python
# tests/test_aster_services.py
import pytest
from unittest.mock import AsyncMock, patch
from app.backend.services.aster_service import AsterMarketDataService

class TestAsterMarketDataService:
    @pytest.fixture
    def service(self):
        config = AsterConfig(
            api_key="test_key",
            secret_key="test_secret",
            base_url="https://test.api"
        )
        return AsterMarketDataService(config)

    @pytest.mark.asyncio
    async def test_fetch_klines_success(self, service):
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = [{"open": 50000, "close": 51000}]
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await service.afetch_klines("BTCUSDT", "1h", 1)
            assert len(result) == 1
            assert result[0]["open"] == 50000

    @pytest.mark.asyncio
    async def test_fetch_klines_rate_limit(self, service):
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.json.return_value = {"code": -1003, "msg": "Too many requests"}
            mock_get.return_value.__aenter__.return_value = mock_response

            with pytest.raises(RateLimitError):
                await service.afetch_klines("BTCUSDT", "1h", 1)
```

### Configuration Management
- **No Global Configs:** Never create global configuration variables or singletons
- **No Function-Based Imports:** Never create functions to import configuration from other files
- **Dependency Injection:** Pass configuration as parameters to functions and classes
- **Local Configuration:** Keep configuration local to each module/class
- **Example Pattern:**
  ```python
  # ❌ BAD: Global config
  _global_config = None

  def get_config():
      global _global_config
      if _global_config is None:
          _global_config = Config()
      return _global_config

  # ❌ BAD: Function-based import
  def get_aster_client(config: AsterConfig) -> AsterClient:
      return AsterClient(config)

  # ✅ GOOD: Direct instantiation with local config
  class DataService:
      def __init__(self, config: DataConfig):
          self.config = config

  # ✅ GOOD: Local configuration
  def create_data_service() -> DataService:
      config = DataConfig(api_key="local_key", base_url="local_url")
      return DataService(config)
  ```

## Coding Style & Naming Conventions
- Python: 4-space indentation, `snake_case` for modules/functions, `PascalCase` for classes; format and sort imports using `ruff`.
- **Python Typing:** Avoid `from typing import List, Dict, Optional, Union`. Prefer built-in types (`list`, `dict`) and use `| None` for optional types and `|` for unions. Prefer constants over raw strings where appropriate.
- **No Future Annotations:** Do not use `from __future__ import annotations` - use direct type annotations instead.
- **Async Function Naming:** Use `a` prefix for async functions instead of `_async` suffix. Examples: `arun_graph()` instead of `run_graph_async()`, `arun_backtest()` instead of `run_backtest_async()`.
- **No Global Configs:** Never create global configuration variables, singletons, or function-based imports for configuration.
- **Local Configuration:** Always keep configuration local to each module/class and pass as parameters.
- **No Private Functions:** Do NOT create private functions (functions prefixed with `_`). All helper functions should be module-level public functions or class methods without underscore prefixes. This improves testability and code reusability.
- **Keep It Simple:** Do NOT over-engineer or create overly complex functions. Start with the simplest solution that works. Avoid unnecessary abstractions, excessive helper functions, or premature optimization. Prefer straightforward, readable code over clever solutions. Refactor only when complexity is genuinely needed.
- **Linting Requirement:** **ALWAYS run linters after coding and fix all issues before committing:**
  - Run `uv run ruff check .` for Python linting
  - Run `uv run ruff format .` for Python formatting
  - Fix all linting errors and warnings before finishing code
  - **Never commit code with linting errors**
- **Docstring Format:** All Python docstrings must follow the NumPy docstring format. Use the following structure:
  ```python
  def function_name(param1: type, param2: type) -> return_type:
      """
      Brief description of the function.

      Parameters
      ----------
      param1 : type
          Description of param1.
      param2 : type
          Description of param2.

      Returns
      -------
      return_type
          Description of the return value.

      Raises
      ------
      ValueError
          Description of when this exception is raised.

      Examples
      --------
      >>> function_name("example", 42)
      "expected output"
      """
  ```
- Ruff, mypy, and gitleaks run through `pre-commit`; install with `pre-commit install`. Always run `pre-commit run --all-files` after any code changes to ensure linting and formatting standards are met before pushing. **All Python code must adhere to the rules defined in `app/backend/ruff.toml`**.
- TypeScript/React: rely on ESLint + Prettier; keep components in PascalCase and hooks in `useCamelCase`.
### Environment Variables
```bash
# .env.example

# API Configuration
API_TITLE="AI Hedge Fund API"
API_DEBUG=false
API_CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"

# Database Configuration
DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/hedge_fund"
DATABASE_ECHO=false

# LLM Configuration
LLM_OPENAI_API_KEY="sk-..."
LLM_OPENAI_API_BASE="https://api.openai.com/v1"
LLM_OPENAI_MODEL="gpt-4-mini"

LLM_ANTHROPIC_API_KEY="sk-ant-..."
LLM_ANTHROPIC_MODEL="claude-3-sonnet-20240229"

LLM_GROQ_API_KEY="gsk_..."
LLM_GROQ_MODEL="llama3-8b-8192"

LLM_DEEPSEEK_API_KEY="sk-..."
LLM_DEEPSEEK_MODEL="deepseek-chat"

LLM_GOOGLE_API_KEY="AIza..."
LLM_GOOGLE_MODEL="gemini-pro"

LLM_OPENROUTER_API_KEY="sk-or-..."
LLM_OPENROUTER_MODEL="openai/gpt-4o-mini"

LLM_LITELLM_API_KEY="sk-..."
LLM_LITELLM_MODEL="gpt-4o-mini"
LLM_LITELLM_BASE_URL="https://api.openai.com/v1"
LLM_LITELLM_TIMEOUT=30
LLM_LITELLM_MAX_TOKENS=4000
LLM_LITELLM_TEMPERATURE=0.7

# Aster Trading Platform
ASTER_API_KEY=your_aster_api_key_here
ASTER_SECRET_KEY=your_aster_secret_key_here
ASTER_BASE_URL=https://api.aster.finance
ASTER_FUTURES_URL=https://fapi.aster.finance
ASTER_WEBSOCKET_URL=wss://stream.aster.finance
ASTER_RATE_LIMIT_PER_MINUTE=1200
ASTER_MAX_RETRIES=3
ASTER_RETRY_DELAY=1

# Redis Configuration
REDIS_URL=redis://localhost:6379
```

### Aster Deployment Considerations
- **API Key Rotation:** Implement automated key rotation for production
- **Rate Limit Monitoring:** Set up alerts for rate limit usage
- **WebSocket Reconnection:** Handle network interruptions gracefully
- **Order Safety:** Implement circuit breakers for order placement
- **Data Backup:** Regular backup of trading data and positions
- **Monitoring:** Track API response times and error rates

## Testing Guidelines
- Prefer `pytest` unit coverage alongside integration checks in `tests/backtesting/integration/`.
- Name test modules `test_*.py` and keep fixtures reusable under `tests/fixtures/`.
- Add regression tests for new agents or risk models and validate failure paths, not just happy flows.
- Surface expected outputs in PRs (e.g., `uv run pytest -q`) when requesting review.

## Commit & Pull Request Guidelines
- Write concise, present-tense commit subjects (≤72 chars) and expand context in the body if needed; group related changes per commit.
- Ensure commits are lint- and test-clean; run `pre-commit run --all-files` and `uv run pytest` before pushing.
- PRs should summarize the change, call out any config updates, link issues, and include CLI or UI screenshots when applicable.
- Tag reviewers early and highlight follow-up work or known gaps in the description.

## UI guidelines

### Document Overview
- **Product Name**: Crypto Pantheon
- **Version**: 1.0
- **Date**: October 25, 2025
- **Purpose**: This design system provides a comprehensive, prescriptive guide for building consistent UI components across the Crypto Pantheon platform. It ensures all elements align with the "Mythic Futurism" theme—merging ancient mythological grandeur (e.g., pantheon temples, divine auras) with cyberpunk crypto aesthetics (e.g., neon circuits, holographic interfaces, blockchain runes). The system prioritizes dark-mode usability, performance visualizations (e.g., PnL charts, leaderboards), and immersive storytelling to evoke FOMO and demonstrate trading agent excellence.

  This document is tailored for AI coding assistants (e.g., in Cursor or similar tools) to generate code without deviations. All components must be modular (using React/Next.js patterns), responsive, accessible (WCAG 2.1 AA compliant), and optimized for performance (e.g., lazy loading for charts). Do not introduce new colors, fonts, or styles outside this spec—adhere strictly to maintain brand integrity.

- **Key Principles**:
  - **Modularity**: All UI elements are built as reusable React components (e.g., via Tailwind CSS classes for styling).
  - **Consistency**: Use predefined tokens (e.g., colors as variables) to avoid variations.
  - **Thematic Immersion**: Elements evoke a "pantheon forge"—holographic glows, subtle animations, cosmic backgrounds.
  - **Performance Focus**: Prioritize data visualizations (charts, metrics) as narrative tools, with clear hierarchies for PnL, win rates, etc.
  - **Accessibility**: High contrast ratios (>4.5:1), ARIA labels, keyboard navigation.
  - **Tech Stack Assumptions**: React/Next.js, Tailwind CSS (for utility classes), Chart.js (for visuals), Framer Motion (for animations), Heroicons or custom SVGs for icons.

### 1. Color Palette
Colors are defined as CSS variables (e.g., in `globals.css` or Tailwind config). Use semantic names for application (e.g., `bg-primary` instead of hex directly). Theme: Cosmic depths with neon energy.

- **Primary Colors**:
  - `--primary-500`: #8B5CF6 (Neon Purple – Accents, CTAs, highlights; evokes divine energy).
  - `--primary-600`: #7C3AED (Darker purple for hovers/active states).
  - `--primary-300`: #A78BFA (Lighter for subtle glows).

- **Secondary Colors**:
  - `--secondary-500`: #10B981 (Emerald Green – Positive metrics, e.g., +PnL; growth/success).
  - `--secondary-600`: #059669 (Darker for hovers).
  - `--secondary-300`: #34D399 (Lighter for charts).

- **Accent Colors**:
  - `--accent-orange`: #F97316 (Fiery Orange – Warnings, high-risk metrics; Aster-inspired action).
  - `--accent-red`: #EF4444 (Red – Negative PnL, losses).
  - `--accent-blue`: #3B82F6 (Blue – Neutral holds, info).

- **Neutral Colors**:
  - `--background`: #0A0A1E (Deep Cosmic Blue-Black – Main BG).
  - `--surface`: #1A1A3A (Darker panel BG for cards/tables).
  - `--text-primary`: #F3F4F6 (Light Gray – Body text).
  - `--text-secondary`: #9CA3AF (Muted Gray – Subtext, labels).
  - `--border`: #2D2D4A (Subtle cosmic border).
  - `--shadow`: rgba(139, 92, 246, 0.2) (Purple glow for shadows/hovers).

- **Usage Rules**:
  - Positive metrics (e.g., +PnL): Green shades.
  - Negative (e.g., drawdown): Red/orange.
  - All elements must maintain contrast: e.g., white text on dark BG.
  - Gradients: Use for BGs, e.g., `bg-gradient-to-r from-[--background] to-[--surface]`.

### 2. Typography
Fonts evoke sleek futurism with mythic subtlety. Use Google Fonts or system fonts for loading speed.

- **Font Families**:
  - Primary: 'Inter', sans-serif (Clean, modern; default for body/headings).
  - Accent: 'Cinzel', serif (Subtle Greek-inspired serifs for headlines/titles; use sparingly for mythic feel).

- **Sizes (Rem-based for scalability)**:
  - `--font-size-xs`: 0.75rem (12px – Fine print, tooltips).
  - `--font-size-sm`: 0.875rem (14px – Labels, subtext).
  - `--font-size-base`: 1rem (16px – Body text).
  - `--font-size-md`: 1.125rem (18px – Subheadings).
  - `--font-size-lg`: 1.25rem (20px – Metrics, cards).
  - `--font-size-xl`: 1.5rem (24px – Section titles).
  - `--font-size-2xl`: 1.875rem (30px – Hero subheads).
  - `--font-size-3xl`: 2.25rem (36px – Hero headlines).
  - `--font-size-4xl`: 3rem (48px – Major emphases).

- **Weights**:
  - 400 (Regular – Body).
  - 500 (Medium – Labels).
  - 600 (Semi-bold – Headings).
  - 700 (Bold – Metrics, CTAs).

- **Line Heights**: 1.5 (default), 1.25 (dense text like tables).
- **Usage Rules**:
  - Headlines: Cinzel for mythic flair (e.g., "Pantheon Arena").
  - Body: Inter everywhere else.
  - Text Shadows: For holographics, e.g., `text-shadow: 0 0 10px var(--primary-300)` on CTAs.
  - Uppercase: Use for badges/labels (e.g., "IN PROGRESS").

### 3. Spacing and Grid System
Consistent rhythm for layouts. Use rem-based spacing.

- **Spacing Scale** (Multiples of 4px base):
  - `--space-1`: 0.25rem (4px – Tight padding).
  - `--space-2`: 0.5rem (8px – Small gaps).
  - `--space-3`: 0.75rem (12px – Default padding).
  - `--space-4`: 1rem (16px – Cards, buttons).
  - `--space-6`: 1.5rem (24px – Sections).
  - `--space-8`: 2rem (32px – Major margins).
  - `--space-12`: 3rem (48px – Hero padding).

- **Grid System**:
  - Default: 12-column responsive grid (Tailwind: grid-cols-12).
  - Breakpoints: Mobile (<640px: stack vertical), Tablet (640-1024px: 2-4 cols), Desktop (>1024px: full grid).
  - Gutters: `--space-4` between columns.

- **Usage Rules**: Always use flex/grid for layouts; no floats. Vertical rhythm: Multiples of `--space-4` for sections.

### 4. Icons and Imagery
- **Icons**: Heroicons (outline/solid) or custom SVGs. Cosmic style: Add glow filters (e.g., SVG filter: blur + color dodge).
  - Sizes: 16px (small), 24px (medium), 32px (large).
  - Colors: Inherit text or use accents (e.g., green check for success).

- **Imagery**:
  - Agent Silhouettes: Holographic deities (e.g., oracle with glowing eyes)—use SVG/PNG with transparency.
  - Backgrounds: Subtle stars/particles (CSS canvas or SVG).
  - Charts/Icons: Neon lines, glowing data points.

- **Animations**: Framer Motion.
  - Entrance: Fade-in (opacity 0→1, 0.5s).
  - Hover: Scale 1.05 + glow (shadow increase).
  - Loading: Pulsing auras (keyframes opacity 0.5→1).
  - Duration: 300ms ease-in-out; no excessive motion.

### 5. Component Library
All components are React functional, with props for variants. Use Tailwind for classes. Export from `/components` folder.

#### 5.1 Buttons
- **Variants**: Primary (neon purple BG), Secondary (green outline), Danger (red).
- **Sizes**: Small (py-2 px-4), Medium (py-3 px-6), Large (py-4 px-8).
- **States**: Default, Hover (brighter glow), Active (scale 0.95), Disabled (opacity 0.5).
- **Example Code**:
  ```jsx
  const Button = ({ variant = 'primary', size = 'medium', children, disabled }) => (
    <button
      className={`rounded-lg font-medium text-white shadow-md hover:shadow-lg transition-all
        ${variant === 'primary' ? 'bg-[--primary-500] hover:bg-[--primary-600]' : ''}
        ${size === 'medium' ? 'py-3 px-6' : ''}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      disabled={disabled}
    >
      {children}
    </button>
  );
  ```

#### 5.2 Cards (e.g., AgentCard)
- **Structure**: Header (title/icon), Body (content), Footer (actions).
- **Variants**: Agent (with hologram image), Metric (with number highlight).
- **Styles**: BG `--surface`, border `--border`, padding `--space-4`, rounded-lg.
- **Example**: For AgentCard – Include deity image, name, traits list.
  ```jsx
  const AgentCard = ({ name, traits, imageUrl }) => (
    <div className="bg-[--surface] border border-[--border] rounded-lg p-[--space-4] shadow-[0_0_10px_var(--primary-300)]">
      <img src={imageUrl} alt={name} className="w-16 h-16 rounded-full mx-auto mb-2 filter drop-shadow-[0_0_5px_var(--primary-500)]" />
      <h3 className="text-lg font-semibold text-[--text-primary]">{name}</h3>
      <ul className="text-sm text-[--text-secondary]">{traits.map(t => <li key={t}>{t}</li>)}</ul>
    </div>
  );
  ```

#### 5.3 Tables (e.g., LeaderboardTable)
- **Structure**: Thead (bold headers), Tbody (rows with alternating BG).
- **Styles**: Border-collapse, cells: p-[--space-2], text-align left.
- **Responsive**: Overflow-x-auto on mobile.
- **Example**:
  ```jsx
  const LeaderboardTable = ({ data }) => (
    <table className="w-full text-[--text-primary] bg-[--surface] rounded-lg overflow-hidden">
      <thead className="bg-[--background]"><tr><th className="p-[--space-3] text-left">Rank</th>...</tr></thead>
      <tbody>
        {data.map(row => (
          <tr key={row.rank} className="border-t border-[--border]">
            <td className="p-[--space-3]">{row.rank}</td>...
          </tr>
        ))}
      </tbody>
    </table>
  );
  ```

#### 5.4 Charts (e.g., PnLChart)
- **Library**: Chart.js (line/bar/pie).
- **Styles**: BG transparent, lines: 2px thick, points: glow on hover.
- **Colors**: Use palette (green for positive, red for negative).
- **Responsive**: MaintainAspectRatio: false.
- **Example** (Line Chart):
  ```jsx
  import { Line } from 'react-chartjs-2';
  const PnLChart = ({ data }) => (
    <div className="p-[--space-4] bg-[--surface] rounded-lg">
      <Line data={data} options={{
        responsive: true,
        scales: { y: { grid: { color: '--border' } } },
        plugins: { legend: { labels: { color: '--text-primary' } } }
      }} />
    </div>
  );
  ```

#### 5.5 Forms (e.g., Sign-Up)
- **Elements**: Inputs (bg-[--background], border-[--border], p-[--space-3]), Labels (text-sm).
- **Validation**: Error text in red.
- **Example**: Input with label.

#### 5.6 Modals/Popups
- **Styles**: Overlay (rgba(0,0,0,0.8)), Content (bg-[--surface], rounded-lg, max-w-md).
- **Animations**: Scale in from 0.95.

#### 5.7 Navigation (Navbar/Sidebar)
- **Navbar**: Fixed top, flex justify-between, links with hover underline.
- **Sidebar**: Vertical, agent list with collapsible sections.

### 6. Layout Patterns
- **Hero**: Full-viewport, centered content.
- **Sections**: Padding `--space-8` top/bottom, max-width 1280px centered.
- **Dashboards**: Grid (sidebar 25%, main 75%).

### 7. Responsiveness and Accessibility
- **Breakpoints**: sm (640px), md (768px), lg (1024px), xl (1280px).
- **Mobile**: Stack cards/tables vertically.
- **Accessibility**: ARIA (e.g., aria-label on icons), focus states (outline purple), alt text on images, semantic HTML.

### 8. Versioning and Updates
- Track changes: e.g., v1.1 for new components.
- Enforcement: AI assistants must reference this doc verbatim—no improvisations.

This system ensures all UI builds are on-brand and consistent. For implementation, start with Tailwind config extensions for variables.

## Anti-Singleton and Import Rules

- Never create singleton globals or module-level instances for engines, clients, or services.
- Never create per-module or function-based import accessors (e.g., `get_engine()` returning a cached/global instance).
- Always use explicit dependency injection: construct objects within request scope or pass them via parameters.
- Keep configuration local to each class/module and pass it in explicitly. Do not centralize via hidden globals.
- Routers and services must not hold global mutable state; prefer short-lived instances per request or well-defined lifecycle managers.

> Rationale: Prevent hidden state, enable testing, and avoid cross-request leakage under ASGI concurrency.
