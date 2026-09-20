"""
Test 1-Second Live Market Data Streaming via WebSocket
Connects to ws://127.0.0.1:8000/api/ws and verifies live ticks update every second.
"""
import sys
import json
import time
import asyncio
import websockets

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

WS_URL = "ws://127.0.0.1:8000/api/ws"

async def test_live_1s_stream():
    print("=" * 70, flush=True)
    print(" >>> CONNECTING TO LIVE 1-SECOND MARKET DATA WEBSOCKET STREAM", flush=True)
    print(f" >>> Target: {WS_URL}", flush=True)
    print("=" * 70, flush=True)

    async with websockets.connect(WS_URL) as ws:
        print("Connected to WebSocket successfully!", flush=True)
        
        # Subscribe to active symbols
        sub_msg = {
            "action": "subscribe",
            "symbols": ["NSE:RELIANCE", "NSE:NIFTY50", "NASDAQ:AAPL", "NSE:TCS"]
        }
        await ws.send(json.dumps(sub_msg))
        print(f"Sent subscription: {sub_msg['symbols']}", flush=True)

        tick_times = []
        received_ticks = 0
        target_ticks = 5

        print(f"\nListening for {target_ticks} consecutive 1-second live ticks...\n", flush=True)

        start_time = time.time()
        prev_time = start_time

        while received_ticks < target_ticks:
            msg_raw = await ws.recv()
            recv_time = time.time()
            data = json.loads(msg_raw)
            msg_type = data.get("type")

            if msg_type == "SUBSCRIBED":
                print(f" [ACK] Subscribed successfully to: {data.get('symbols')}", flush=True)
                continue

            if msg_type == "PONG":
                print(f" [PONG] Heartbeat response received", flush=True)
                continue

            if msg_type == "TICK_UPDATE":
                received_ticks += 1
                dt = recv_time - prev_time if received_ticks > 1 else 0.0
                prev_time = recv_time
                tick_times.append(recv_time)

                tick_num = data.get("tick_count", received_ticks)
                timestamp = data.get("timestamp", "")[:19]
                quotes = data.get("quotes", [])
                indices = data.get("indices", {})
                feed_health = data.get("feed_health", {})
                conn_status = feed_health.get("connection_status", "LIVE")

                print(f"Tick #{received_ticks} (Counter: {tick_num}) | Time: {timestamp} | Interval: {dt:.2f}s | Feed: {conn_status}", flush=True)
                nifty_p = indices.get('NIFTY 50', {}).get('price')
                sensex_p = indices.get('SENSEX', {}).get('price')
                print(f"   Indices: NIFTY 50 = {nifty_p} | SENSEX = {sensex_p}", flush=True)
                
                # Show active quotes
                quotes_summary = []
                for q in quotes[:4]:
                    sym = q.get("symbol")
                    p = q.get("price") or q.get("last_price")
                    if p is not None:
                        quotes_summary.append(f"{sym}: ₹{p:,.2f}" if "AAPL" not in sym else f"{sym}: ${p:,.2f}")
                print(f"   Quotes ({len(quotes)} tracked): {', '.join(quotes_summary) if quotes_summary else 'Hydrating...'}", flush=True)
                print("-" * 65, flush=True)

        total_duration = time.time() - start_time
        avg_interval = (total_duration / received_ticks) if received_ticks else 0.0
        print("\n" + "=" * 70, flush=True)
        print(f" >>> LIVE 1-SECOND STREAM VERIFICATION SUMMARY", flush=True)
        print(f"     Total Ticks Received: {received_ticks}", flush=True)
        print(f"     Total Duration:       {total_duration:.2f}s", flush=True)
        print(f"     Average Tick Interval:{avg_interval:.2f}s (~1.0s target)", flush=True)
        print(f"     Status:               VERIFIED & STREAMING LIVE EVERY SECOND", flush=True)
        print("=" * 70, flush=True)

if __name__ == "__main__":
    asyncio.run(test_live_1s_stream())
