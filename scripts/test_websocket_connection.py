"""Test WebSocket council trades connection."""

import asyncio
import json

import websockets


async def test_websocket():
    """
    Test WebSocket connection to /ws/council-trades endpoint.

    This script connects to the WebSocket, sends a ping, subscribes to council updates,
    and waits for responses.
    """
    uri = "ws://localhost:8000/ws/council-trades"

    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")

            # Send a ping
            print("\nSending ping...")
            await websocket.send(json.dumps({"type": "ping"}))

            # Wait for pong response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Received: {data}")

            if data.get("type") == "pong":
                print("✅ Ping/pong works!")

            # Subscribe to a council
            print("\nSubscribing to council ID 1...")
            await websocket.send(
                json.dumps({"type": "subscribe_council", "council_id": 1})
            )

            # Wait for subscription confirmation
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Received: {data}")

            if data.get("type") == "subscription_confirmed":
                print("✅ Subscription confirmed!")

            # Keep connection open and listen for messages
            print("\nListening for messages (10 seconds)...")
            try:
                async with asyncio.timeout(10):
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        print(f"📨 Received message: {data}")
            except TimeoutError:
                print("\n⏱️ Timeout reached (10 seconds)")

            print("\n✅ WebSocket test completed successfully!")

    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
    except ConnectionRefusedError:
        print("❌ Connection refused. Is the backend running?")
        print(
            "   Start it with: uv run uvicorn main:app --reload --app-dir app/backend"
        )
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    print("WebSocket Council Trades Test")
    print("=" * 50)
    asyncio.run(test_websocket())
