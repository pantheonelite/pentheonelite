# Council Data Reset Script - Quick Reference

## Overview

The `reset_council_data.py` script provides a safe way to delete council-related data for local testing. It includes safety confirmations and detailed reporting.

## Quick Start

### Delete All Data (Most Common)

```bash
# With confirmation prompt (recommended)
uv run python scripts/reset_council_data.py --all

# Skip confirmation (use with caution)
uv run python scripts/reset_council_data.py --all --yes
```

### Delete Specific Councils

```bash
# Delete councils by ID
uv run python scripts/reset_council_data.py --councils 1 2 3
```

### Delete Only System Councils

```bash
# Delete system councils (is_system=true) only
uv run python scripts/reset_council_data.py --system-only
```

## What Gets Deleted

The script deletes all related data in the correct order to respect foreign key constraints:

1. **Council Run Cycles** (`council_run_cycles_v2`)
2. **Council Runs** (`council_runs_v2`)
3. **Agent Debates** (`agent_debates`)
4. **Performance Snapshots** (`council_performance`)
5. **Market Orders** (`market_orders`) - includes spot trading orders
6. **Portfolio Holdings** (`portfolio_holdings`) - spot trading holdings
7. **Councils** (`councils`)

## Usage Examples

### Scenario 1: Clean Slate for Testing

```bash
# Start fresh
$ uv run python scripts/reset_council_data.py --all

⚠️  WARNING: DESTRUCTIVE OPERATION ⚠️
This will DELETE ALL council-related data including:
  - All councils (system and user)
  - All market orders/trades
  - All portfolio holdings
  ...

Type 'DELETE ALL' to confirm: DELETE ALL

📊 Current data counts:
  - councils: 5
  - market_orders: 23
  - portfolio_holdings: 8
  - council_runs: 12
  - council_run_cycles: 48
  - agent_debates: 35
  - council_performance: 156

🗑️  Deleting data...
✅ Deletion complete!

📊 Deleted records:
  - Council run cycles: 48
  - Council runs: 12
  - Agent debates: 35
  - Performance snapshots: 156
  - Market orders: 23
  - Portfolio holdings: 8
  - Councils: 5

  Total records deleted: 287
```

### Scenario 2: Remove Failed Test Councils

```bash
# Remove specific test councils
$ uv run python scripts/reset_council_data.py --councils 42 43 44

⚠️  Delete councils [42, 43, 44]? (y/N): y
✅ Deleted council 42 (Test Debate Council)
✅ Deleted council 43 (Test Trading Council)
✅ Deleted council 44 (Test Full Cycle Council)

✅ Successfully deleted 3 council(s)
```

### Scenario 3: Reset System Councils Only

```bash
# Keep user councils, delete system ones
$ uv run python scripts/reset_council_data.py --system-only

⚠️  Delete all system councils? (y/N): y

📊 Found 3 system councils:
  - 1: Alpha Trading Council
  - 2: Beta Risk Council
  - 3: Gamma Momentum Council

✅ Deleted 3 system council(s) and their related data
```

### Scenario 4: Automated Testing Scripts

```bash
# In a test script - skip confirmation
uv run python scripts/reset_council_data.py --all --yes
```

## Safety Features

### 1. Confirmation Prompts

The script requires explicit confirmation for destructive operations:

- `--all`: Must type "DELETE ALL" exactly
- `--system-only`: Must confirm with 'y'
- `--councils`: Must confirm with 'y'
- `--yes`: Skips all prompts (use carefully!)

### 2. Data Counts

Before deletion, the script shows exactly what will be deleted:

```
📊 Current data counts:
  - councils: 5
  - market_orders: 23
  - portfolio_holdings: 8
  ...
```

### 3. Detailed Reporting

After deletion, see exactly what was removed:

```
📊 Deleted records:
  - Council run cycles: 48
  - Council runs: 12
  - Agent debates: 35
  ...
```

### 4. Transaction Rollback

If any error occurs during deletion, all changes are rolled back.

## Integration with Testing Workflow

### Before Each Test Run

```bash
# 1. Reset data
uv run python scripts/reset_council_data.py --all

# 2. Run migrations (if needed)
cd app/backend && alembic upgrade head && cd ../..

# 3. Run tests
uv run python scripts/test_debate_flow.py --symbols BTCUSDT,ETHUSDT
```

### In CI/CD Pipeline

```bash
#!/bin/bash
# Test script with automated cleanup

# Reset data without prompts
uv run python scripts/reset_council_data.py --all --yes

# Run your tests
uv run pytest tests/

# Cleanup after tests
uv run python scripts/reset_council_data.py --all --yes
```

## Command-Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--all` | Delete all council data | `--all` |
| `--councils ID [ID ...]` | Delete specific councils | `--councils 1 2 3` |
| `--system-only` | Delete only system councils | `--system-only` |
| `--yes` | Skip confirmation prompts | `--all --yes` |

## Help

```bash
# Show help and examples
uv run python scripts/reset_council_data.py

# Or with --help flag
uv run python scripts/reset_council_data.py --help
```

## Troubleshooting

### "No data to delete"

```bash
$ uv run python scripts/reset_council_data.py --all
...
✅ No data to delete - database is already clean
```

**Solution:** Database is empty, no action needed.

### "Council X not found"

```bash
$ uv run python scripts/reset_council_data.py --councils 999
⚠️  Council 999 not found - skipping
✅ Successfully deleted 0 council(s)
```

**Solution:** Check council IDs in database or use `--all` to delete everything.

### Database Connection Error

```bash
$ uv run python scripts/reset_council_data.py --all
❌ Operation failed: connection refused
```

**Solution:**
- Ensure PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Verify database exists

### Foreign Key Constraint Errors

The script deletes in the correct order to avoid foreign key violations. If you see this error, it's likely a bug in the script.

**Solution:** Report the issue with full error details.

## Best Practices

### ✅ Do's

- **Use `--all` for complete reset** before major testing
- **Use `--councils` to clean up specific tests** without affecting others
- **Check data counts** before confirming deletion
- **Use in CI/CD** with `--yes` flag for automated testing
- **Keep backups** of important test data

### ❌ Don'ts

- **Don't use in production** - this is for local/testing only
- **Don't skip confirmations** unless you're certain
- **Don't interrupt** during deletion (Ctrl+C is safe but leaves partial state)
- **Don't run multiple instances** simultaneously

## Related Scripts

- `migrate_spot_trading_data.py` - Migrate existing data to spot trading schema
- `test_debate_flow.py` - Test agent debates after reset
- `test_trading_flow.py` - Test trading after reset
- `test_full_cycle.py` - Test complete cycle after reset

## Advanced Usage

### Reset and Recreate Test Data

```bash
# 1. Reset all data
uv run python scripts/reset_council_data.py --all --yes

# 2. Run migration (if schema changed)
cd app/backend && alembic upgrade head && cd ../..

# 3. Create test councils
uv run python scripts/test_debate_flow.py --create-council --symbols BTCUSDT,ETHUSDT
```

### Selective Cleanup in Tests

```python
# In a pytest fixture
import subprocess

@pytest.fixture
async def clean_councils():
    """Clean up test councils before/after tests."""
    # Before test
    subprocess.run([
        "uv", "run", "python", "scripts/reset_council_data.py",
        "--councils", "42", "43", "--yes"
    ])

    yield

    # After test
    subprocess.run([
        "uv", "run", "python", "scripts/reset_council_data.py",
        "--councils", "42", "43", "--yes"
    ])
```

## Summary

The reset script is your go-to tool for:
- 🧹 **Clean testing environments**
- 🔄 **Reproducible test runs**
- 🎯 **Focused council cleanup**
- ⚡ **Quick iteration during development**

**Remember:** This is a powerful tool - use it wisely! Always confirm you're running against the correct database before deletion.
