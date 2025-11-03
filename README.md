
# AI Hedge Fund

AI-powered, multi-agent trading research platform. This project explores agentic decision-making for markets across fundamentals, sentiment, technicals, and risk—built for education and experimentation, not live trading.

## Highlights
- Multi-agent architecture (valuation, sentiment, fundamentals, technicals, risk, portfolio)
- Async-first Python services with FastAPI backend and Vite + React frontend
- Simple CLI for quick experiments; optional web UI for visualization
- Backtesting utilities for offline evaluation

## Architecture
- `src/`: Trading graph, agents, tools, and CLI entry points (`main.py`, `backtester.py`)
- `app/backend/`: FastAPI service (routes, services, database, alembic)
- `app/frontend/`: Vite + React dashboard (Tailwind, charts)
- `tests/`: Pytest suites (fixtures, integration scenarios)
- `docker/`: Local/CI runtime images and scripts

Agents (mapped to source):
- Market analysts: `app/backend/src/agents/analyst/crypto_analyst.py`, `app/backend/src/agents/analyst/crypto_sentiment.py`, `app/backend/src/agents/analyst/crypto_technical.py`
- Crypto personas: `app/backend/src/agents/analyst/elon_musk.py`, `app/backend/src/agents/analyst/michael_saylor.py`, `app/backend/src/agents/analyst/satoshi_nakamoto.py`, `app/backend/src/agents/analyst/vitalik_buterin.py`, `app/backend/src/agents/analyst/cz_binance.py`, `app/backend/src/agents/analyst/defi_agent.py`
- Traders: `app/backend/src/agents/trader_agent.py`, `app/backend/src/agents/futures_trading_agent.py`
- Risk: `app/backend/src/agents/crypto_risk_manager.py`
- Portfolio: `app/backend/src/agents/portfolio_manager.py`


## Quickstart

### Prereqs
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

### Install
```bash
git clone https://github.com/pantheonelite/pentheonelite
cd pentheonelite
```

### Configure
```bash
cp .env.example .env
# edit .env and set at least one LLM key (e.g., OPENAI_API_KEY)
```

Crypto-first setup: public market data for major pairs (e.g., BTCUSDT, ETHUSDT) may be accessible without keys, but authenticated endpoints and trading require Aster credentials. Set `ASTER_API_KEY` and `ASTER_SECRET_KEY` in `.env`. Optional: Binance (spot/futures) keys if using Binance clients.

### Run (CLI)
```bash
uv run python src/main.py --ticker BTCUSDT,ETHUSDT
uv run python src/main.py --ticker BTCUSDT,ETHUSDT --start-date 2024-01-01 --end-date 2024-03-01
```

### Backtest (CLI)
```bash
uv run python src/backtester.py --ticker BTCUSDT,ETHUSDT
uv run python src/backtester.py --ticker BTCUSDT,ETHUSDT --start-date 2024-01-01 --end-date 2024-03-01
```

### Examples
```bash
# Run aggressive futures trading demo
uv run python examples/aggressive_futures_trading.py

# Try LangChain tool tests
uv run python examples/test_langchain_tools.py
```

## Web Application
Start the FastAPI backend and the Vite + React frontend.

1) Configure environment
```bash
cp .env.example .env
# set ASTER_API_KEY, ASTER_SECRET_KEY, and CORS origins if needed
```

2) Initialize database (PostgreSQL)
```bash
bash scripts/setup_database.sh
```

3) Start backend (FastAPI)
```bash
uv run uvicorn main:app --reload --app-dir app/backend
```

4) Start frontend (Vite + React)
```bash
cd app/frontend && pnpm install && pnpm dev
```

Access:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Docs: http://localhost:8000/docs

## Docker (Optional)
For a consistent local stack with PostgreSQL, backend, and frontend:
```bash
docker compose up -d           # start services (see docker-compose.yml)
docker compose logs -f         # follow logs
docker compose down            # stop and remove
```

## Development
- Lint/format: `uv run ruff check .` and `uv run ruff format .`
- Tests: `uv run pytest` (add `-k` to filter)
- Pre-commit: `pre-commit install` then `pre-commit run --all-files`

Project conventions:
- Async methods use the `a` prefix (e.g., `arun_backtest`)
- Pydantic schemas live under `app/backend/api/schemas/`
- Alembic migration naming: `000x_description.py`

Convenience scripts (optional):
```bash
bash scripts/start-backend.sh        # start FastAPI with sensible defaults
bash scripts/stop_all_services.sh    # stop services started via scripts
```

## Key Services (Backend)
- `AgentService`, `GraphService`, `PortfolioService`
- `BacktestService`, `CryptoBacktestService`
- `Council*` services for orchestration and metrics
- `UnifiedTradingService`, `FuturesPositionService`, `SpotHoldingService`

## Aster Finance Integration
- Clients and config under `app/backend/client/aster` and `app/backend/config/aster.py`
- Supports market data and trading via Aster endpoints (Spot/Futures/WebSocket)
- Configure API keys in `.env` (see `.env.example`)

Also available:
- Binance clients under `app/backend/client/binance` and config in `app/backend/config/binance.py`

Connectivity test (Aster):
```bash
uv run python -m app.backend.src.tools.aster.test_connection
```

## Councils & Orchestrator (scripts/)
Load council data and run the long-lived orchestrator daemon.

1) Load mock council data
```bash
# Option A: shell wrapper
bash scripts/load_mock_data.sh

# Option B: Python loader (more control)
uv run python scripts/load_mock_data_councils.py
```

2) Run the orchestrator daemon
```bash
# Start (daemonized via helper script)
bash scripts/start_orchestrator.sh

# Check status
bash scripts/status_orchestrator.sh

# Stop daemon
bash scripts/stop_orchestrator.sh
```

Alternative (foreground for debugging):
```bash
uv run python scripts/run_orchestrator.py
```

3) Utilities
```bash
# Verify councils were loaded
uv run python scripts/check_councils.py

# Reset council datasets (DANGER: destructive)
uv run python scripts/reset_council_data.py
```

## Contributing
1. Fork the repo
2. Create a feature branch
3. Keep edits small and focused
4. Open a PR with a clear summary and test results

Issues and feature requests: open an issue and tag `enhancement`.

## Disclaimer
This project is for educational and research purposes only.
- No investment advice; no live trading
- No guarantees; use at your own risk
- Past performance does not indicate future results

## License
MIT — see `LICENSE`.
