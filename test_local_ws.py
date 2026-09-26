import asyncio
import websockets

URL = "ws://127.0.0.1:8000/api/ws"

async def main():
    print("Connecting to:", URL)

    try:
        async with websockets.connect(URL, open_timeout=15) as ws:
            print("? WEBSOCKET CONNECTED")
            print("Waiting for backend message...")

            try:
                message = await asyncio.wait_for(ws.recv(), timeout=10)
                print("?? BACKEND MESSAGE:")
                print(message)
            except asyncio.TimeoutError:
                print("?? Connected, but no message received in 10 seconds.")

    except Exception as e:
        print("? WEBSOCKET CONNECTION FAILED")
        print(type(e).__name__, ":", e)

asyncio.run(main())
