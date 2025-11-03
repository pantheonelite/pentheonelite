"""Test script for Binance Testnet futures trading."""

import asyncio

import structlog

from app.backend.client.binance import BinanceClient, BinanceConfig
from app.backend.config.binance import get_binance_settings

logger = structlog.get_logger(__name__)


async def test_binance_testnet():
    """Test Binance Testnet connection and basic operations."""
    print("=" * 80)
    print("Testing Binance Testnet Futures Connection")
    print("=" * 80)

    # Initialize client
    binance_settings = get_binance_settings()
    config = BinanceConfig(
        api_key=binance_settings.api_key,
        api_secret=binance_settings.api_secret,
        testnet=True,
    )

    client = BinanceClient(config, enable_rate_limiting=True)

    print("\n✅ Client initialized")
    print(f"   Base URL: {client.base_url}")
    print(f"   Testnet: {config.testnet}")

    try:
        # Test 1: Get account info
        print("\n" + "=" * 80)
        print("TEST 1: Account Information")
        print("=" * 80)

        account = await client.aget_account_info()
        print("✅ Account fetched successfully")
        print(f"   Total Balance: ${account.total_balance:,.2f}")
        print(f"   Available Balance: ${account.available_balance:,.2f}")
        print(f"   Used Balance: ${account.used_balance:,.2f}")
        print(f"   Unrealized PnL: ${account.unrealized_pnl:,.2f}")

        # Test 2: Get ticker
        print("\n" + "=" * 80)
        print("TEST 2: Market Data")
        print("=" * 80)

        ticker = await client.aget_ticker("BTCUSDT")
        print("✅ Ticker fetched successfully")
        print(f"   Symbol: {ticker.symbol}")
        print(f"   Price: ${ticker.price:,.2f}")
        print(f"   24h Volume: ${ticker.volume:,.2f}")
        print(f"   24h Change: {ticker.change_percent_24h:,.2f}%")

        # Test 3: Get current positions
        print("\n" + "=" * 80)
        print("TEST 3: Current Positions")
        print("=" * 80)

        positions = await client.aget_positions()
        print(f"✅ Positions fetched: {len(positions)} positions")

        if positions:
            for pos in positions:
                print(f"\n   Position: {pos.symbol}")
                print(f"   - Side: {pos.position_side}")
                print(f"   - Amount: {pos.position_amount}")
                print(f"   - Entry Price: ${pos.entry_price:,.2f}")
                print(f"   - Mark Price: ${pos.mark_price:,.2f}")
                print(f"   - Unrealized PnL: ${pos.unrealized_pnl:,.2f}")
                print(f"   - Leverage: {pos.leverage}x")
                if pos.liquidation_price:
                    print(f"   - Liquidation Price: ${pos.liquidation_price:,.2f}")
        else:
            print("   No open positions")

        # Test 4: Symbol info
        print("\n" + "=" * 80)
        print("TEST 4: Symbol Information")
        print("=" * 80)

        symbol_info = await client.aget_symbol_info("BTCUSDT")
        print("✅ Symbol info fetched")
        print(f"   Symbol: {symbol_info.get('symbol')}")
        print(f"   Status: {symbol_info.get('status')}")
        print(f"   Contract Type: {symbol_info.get('contractType')}")

        filters = symbol_info.get("filters", [])
        for f in filters:
            if f.get("filterType") == "LOT_SIZE":
                print(f"   Min Quantity: {f.get('minQty')}")
                print(f"   Max Quantity: {f.get('maxQty')}")
                print(f"   Step Size: {f.get('stepSize')}")

        # Test 5: Place small test order (if balance available)
        if account.available_balance > 100:
            print("\n" + "=" * 80)
            print("TEST 5: Place Test Order (OPTIONAL)")
            print("=" * 80)
            print("⚠️  Skipping order placement to avoid testnet changes")
            print("   To test order placement, uncomment the code in the script")

            # Uncomment to test order placement:
            # order = await client.aplace_order(
            #     symbol="BTCUSDT",
            #     side="BUY",
            #     order_type="MARKET",
            #     quantity=0.001,
            #     position_side="LONG"
            # )
            # print(f"✅ Order placed")
            # print(f"   Order ID: {order.order_id}")
            # print(f"   Status: {order.status}")

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print("\nBinance Testnet is ready for position-based trading!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.exception("Binance testnet test failed", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(test_binance_testnet())
