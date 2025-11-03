# Council Testing Scripts

Executable test scripts for manual testing of council services with real database and API interactions.

## Overview

These scripts allow you to test individual components and the complete council trading cycle without mocks. They interact with:
- Real database (PostgreSQL)
- Real ASTER API (with --test-mode flag to skip orders)
- Real agent workflows (`run_crypto_hedge_fund`)

## Scripts

### 0. `reset_council_data.py` - Reset Council Data for Testing

Quickly delete council-related data for clean local testing.

**Usage:**
```bash
# Delete all council data (with confirmation)
uv run python scripts/reset_council_data.py --all

# Delete specific councils by ID
uv run python scripts/reset_council_data.py --councils 1 2 3

# Delete only system councils
uv run python scripts/reset_council_data.py --system-only

# Delete all without confirmation (dangerous!)
uv run python scripts/reset_council_data.py --all --yes
```

**What it deletes:**
- ✓ All councils (system and user)
- ✓ All market orders/trades
- ✓ All portfolio holdings
- ✓ All council runs and cycles
- ✓ All agent debates
- ✓ All council performance snapshots

**Output:**
- Data counts before deletion
- Deletion confirmation prompt
- Summary of deleted records

**⚠️ WARNING:** This is DESTRUCTIVE! Only use for local testing.

---

### 1. `test_debate_flow.py` - Test Agent Debate & Consensus

Tests the debate execution and consensus determination flow.

**Usage:**
```bash
# Create new test council and run debate (symbols required)
uv run python scripts/test_debate_flow.py --symbols BTCUSDT,ETHUSDT

# Use existing council with custom symbols
uv run python scripts/test_debate_flow.py --symbols BTCUSDT,ETHUSDT --council-id 1

# Test with different crypto pairs
uv run python scripts/test_debate_flow.py --symbols SOLUSDT,AVAXUSDT

# Custom consensus threshold
uv run python scripts/test_debate_flow.py --symbols BTCUSDT,ETHUSDT --threshold 0.7
```

**What it tests:**
- ✓ Agent debate execution via `run_crypto_hedge_fund`
- ✓ Signal parsing from workflow results
- ✓ Consensus determination with vote counting
- ✓ Database storage of debate messages
- ✓ Consensus message logging

**Output:**
- Agent signals with action, sentiment, confidence
- Consensus decision with vote breakdown
- Database verification of stored messages

---

### 2. `test_trading_flow.py` - Test Order Execution & PnL

Tests the trade execution and database logging flow.

**Usage:**
```bash
# Paper trading mode (no real orders - RECOMMENDED FIRST)
uv run python scripts/test_trading_flow.py --council-id 1 --symbol BTCUSDT --paper-trading

# Real order execution (CAUTION! - symbols required)
uv run python scripts/test_trading_flow.py --council-id 1 --symbol BTCUSDT --decision BUY

# Sell order with different symbol
uv run python scripts/test_trading_flow.py --council-id 1 --symbol ETHUSDT --decision SELL

# Test with alternative crypto
uv run python scripts/test_trading_flow.py --council-id 1 --symbol SOLUSDT --decision BUY --paper-trading
```

**What it tests:**
- ✓ Order parameter calculation (position sizing, quantity precision)
- ✓ ASTER API integration (price fetching, order placement)
- ✓ Database order record creation
- ✓ PnL calculation and updates
- ✓ Performance snapshot creation

**Output:**
- Order details (ID, symbol, quantity, price)
- Database records (orders, performance snapshots)
- Current portfolio state

**⚠️ WARNING:** Without `--test-mode`, this will place REAL orders on ASTER!

---

### 3. `test_full_cycle.py` - Test Complete Council Cycle

Tests the end-to-end council trading cycle: debate → consensus → trade → PnL.

**Usage:**
```bash
# Test mode with existing council (RECOMMENDED - symbols required)
uv run python scripts/test_full_cycle.py --council-id 1 --symbols BTCUSDT,ETHUSDT --test-mode

# Create new council and run full cycle in test mode
uv run python scripts/test_full_cycle.py --create-council --symbols BTCUSDT,ETHUSDT --test-mode

# Test with different crypto pairs
uv run python scripts/test_full_cycle.py --council-id 1 --symbols SOLUSDT,AVAXUSDT --test-mode

# Live mode with real orders (CAUTION!)
uv run python scripts/test_full_cycle.py --council-id 1 --symbols BTCUSDT,ETHUSDT
```

**What it tests:**
- ✓ Complete workflow integration
- ✓ Service composition (DebateService + CouncilTradingService)
- ✓ Database state consistency across phases
- ✓ Error handling and rollback
- ✓ Performance tracking

**Output:**
- Phase-by-phase progress
- Complete cycle summary
- Database verification results

---

## Prerequisites

1. **Database Setup:**
   ```bash
   # Ensure PostgreSQL is running and database is migrated
   cd app/backend
   alembic upgrade head

   # Optional: Reset data for clean testing
   cd ../..
   uv run python scripts/reset_council_data.py --all
   ```

2. **Environment Variables:**
   ```bash
   # Required in .env
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/hedge_fund

   # For real orders
   ASTER_API_KEY=your_api_key
   ASTER_SECRET_KEY=your_secret_key

   # For agent debates
   LLM_OPENROUTER_API_KEY=your_openrouter_key
   ```

3. **Council Setup:**
   ```bash
   # Create a system council or use existing one
   # Check available councils:
   uv run python -c "from app.backend.db.session import get_session; from app.backend.db.repositories.council_repository import CouncilRepository; import asyncio; async def main(): async for session in get_session(): councils = await CouncilRepository(session).get_system_councils(); print([c.id for c in councils]); break; asyncio.run(main())"
   ```

## Testing Workflow

### Recommended Testing Sequence:

0. **Reset data for clean testing (optional):**
   ```bash
   uv run python scripts/reset_council_data.py --all
   ```

1. **Start with debate testing (symbols required):**
   ```bash
   uv run python scripts/test_debate_flow.py --symbols BTCUSDT,ETHUSDT
   # Note the council_id from output
   ```

2. **Test trading in paper trading mode:**
   ```bash
   uv run python scripts/test_trading_flow.py --council-id <ID> --symbol BTCUSDT --paper-trading
   ```

3. **Run full cycle in test mode:**
   ```bash
   uv run python scripts/test_full_cycle.py --council-id <ID> --symbols BTCUSDT,ETHUSDT --test-mode
   ```

4. **When ready, test with real orders (small amounts!):**
   ```bash
   uv run python scripts/test_trading_flow.py --council-id <ID> --symbol BTCUSDT --decision BUY
   ```

### Example Session:

```bash
# 0. Reset data for clean start
$ uv run python scripts/reset_council_data.py --all
⚠️  WARNING: DESTRUCTIVE OPERATION ⚠️
Type 'DELETE ALL' to confirm: DELETE ALL
✅ Deletion complete!
Total records deleted: 156

# 1. Test debate execution (symbols required)
$ uv run python scripts/test_debate_flow.py --symbols BTCUSDT,ETHUSDT
🧪 Testing Debate Flow
...
✅ Created test council: Test Debate Council (ID: 42)
✅ Debate completed successfully
✅ Consensus Decision: BUY

# 2. Test order creation (paper trading mode)
$ uv run python scripts/test_trading_flow.py --council-id 42 --symbol BTCUSDT --paper-trading
🧪 Testing Trading Flow
...
📝 PAPER TRADING MODE: Orders will be simulated (no real execution)
✅ Paper order simulated successfully!

# 3. Test full cycle with symbols
$ uv run python scripts/test_full_cycle.py --council-id 42 --symbols BTCUSDT,ETHUSDT --test-mode
🧪 Testing Full Council Cycle
...
✅ Full cycle completed successfully!
```

## Troubleshooting

### "Council not found"
- Create a council first with `--create-council` flag
- Or check existing councils in database

### "LLM API Error"
- Verify OpenRouter API key is set in `.env`
- Check API quota/limits

### "ASTER API Error"
- Verify ASTER credentials in `.env`
- Use `--test-mode` to skip API calls

### "Database Error"
- Ensure PostgreSQL is running
- Run migrations: `uv run alembic upgrade head`
- Check database connection string

## Safety Notes

- **ALWAYS use `--test-mode` flag** when testing for the first time
- Real orders will be placed on ASTER if `--test-mode` is not specified
- Start with small test amounts when testing real orders
- Monitor database state between test runs
- Keep test councils separate from production councils

## Development

These scripts are designed for:
- Manual testing during development
- Debugging service integration
- Verifying database logging
- Testing API integration
- Demonstrating functionality

For automated testing, see `tests/` directory for pytest-based unit tests.
