"""
WebSocket Market Stream Manager — TradePilot

Manages all client WebSocket connections for real-time market data streaming.

Features:
  - Per-client symbol subscription tracking
  - Route QUOTE_UPDATE only to subscribed clients
  - Broadcast MARKET_STATUS to all clients
  - Broadcast FEED_STATUS on connect/disconnect events
  - Stale data warning broadcasts
  - Clean disconnection handling

WebSocket protocol:

Client → Server:
  Subscribe:   {"action": "subscribe",   "symbols": ["NSE:NIFTY50", "NSE:RELIANCE"]}
  Unsubscribe: {"action": "unsubscribe", "symbols": ["NSE:RELIANCE"]}
  Ping:        {"action": "ping"}

Server → Client:
  Snapshot:      {"type": "SNAPSHOT",      "market_status": {...}, "quotes": [...]}
  Quote update:  {"type": "QUOTE_UPDATE",  "symbol": "...", "last_price": ..., ...}
  Market status: {"type": "MARKET_STATUS", "status": "OPEN", ...}
  Feed status:   {"type": "FEED_STATUS",   "status": "CONNECTED" | "DISCONNECTED"}
  Pong:          {"type": "PONG"}
"""
import asyncio
import json
import logging
from typing import Dict, Set, List, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketMarketStreamManager:
    """
    Manages client WebSocket connections for real-time market data streaming.

    Each client maintains its own symbol subscription set.
    QUOTE_UPDATE messages are only sent to clients subscribed to that symbol.
    MARKET_STATUS and FEED_STATUS are broadcast to all clients.
    """

    def __init__(self):
        # Maps WebSocket → set of subscribed symbols
        self._client_subscriptions: Dict[WebSocket, Set[str]] = {}
        self._lock = asyncio.Lock()

    @property
    def active_connections(self) -> Set[WebSocket]:
        return set(self._client_subscriptions.keys())

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket client and initialize with empty subscription."""
        await websocket.accept()
        async with self._lock:
            self._client_subscriptions[websocket] = set()
        logger.info(
            f"WebSocket: client connected. "
            f"Total active: {len(self._client_subscriptions)}"
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a client and its subscriptions."""
        async with self._lock:
            self._client_subscriptions.pop(websocket, None)
        logger.info(
            f"WebSocket: client disconnected. "
            f"Total active: {len(self._client_subscriptions)}"
        )

    async def handle_client_message(self, websocket: WebSocket, raw_message: str) -> None:
        """
        Process an incoming client message.

        Supported actions: subscribe, unsubscribe, ping
        """
        try:
            msg = json.loads(raw_message)
        except (json.JSONDecodeError, ValueError):
            return

        action = msg.get("action", "").lower()
        symbols = [s.upper() for s in msg.get("symbols", [])]

        if action == "subscribe" and symbols:
            async with self._lock:
                if websocket in self._client_subscriptions:
                    self._client_subscriptions[websocket].update(symbols)
            logger.info(f"WebSocket: client subscribed to {symbols}")
            # Confirm subscription
            await self._safe_send(websocket, {
                "type": "SUBSCRIBED",
                "symbols": symbols,
                "message": "Subscribed. Updates will begin shortly.",
            })

        elif action == "unsubscribe" and symbols:
            async with self._lock:
                if websocket in self._client_subscriptions:
                    self._client_subscriptions[websocket].difference_update(symbols)
            logger.info(f"WebSocket: client unsubscribed from {symbols}")

        elif action == "ping":
            await self._safe_send(websocket, {"type": "PONG", "timestamp": _now_iso()})

    async def broadcast_quote_update(self, quote: Dict[str, Any]) -> None:
        """
        Send QUOTE_UPDATE to all clients subscribed to this symbol.

        A client receives the update if:
          - They have subscribed to this exact symbol (e.g., "NSE:RELIANCE" or "RELIANCE")
          - They have an empty subscription set (receives all quotes — legacy mode)
        """
        symbol = quote.get("symbol", "")
        exchange = quote.get("exchange", "NSE")
        symbol_keys = {
            symbol,
            f"{exchange}:{symbol}",
            f"{symbol}.NS",
            f"{symbol}.BO",
        }

        payload = {
            "type":             "QUOTE_UPDATE",
            "symbol":           symbol,
            "exchange":         exchange,
            "last_price":       quote.get("last_price"),
            "open":             quote.get("open"),
            "high":             quote.get("high"),
            "low":              quote.get("low"),
            "previous_close":   quote.get("previous_close"),
            "change":           quote.get("change"),
            "change_percent":   quote.get("change_percent"),
            "volume":           quote.get("volume"),
            "bid_price":        quote.get("bid_price"),
            "ask_price":        quote.get("ask_price"),
            "data_status":      quote.get("data_status", "LIVE_DELAYED"),
            "data_source":      quote.get("data_source"),
            "data_delay_minutes": quote.get("data_delay_minutes"),
            "timestamp":        quote.get("timestamp"),
            "is_live":          quote.get("is_live", False),
        }

        dead_connections = set()
        async with self._lock:
            for ws, subs in list(self._client_subscriptions.items()):
                # Empty subs = legacy mode (receives all quotes)
                if len(subs) == 0 or bool(subs & symbol_keys):
                    if not await self._safe_send(ws, payload):
                        dead_connections.add(ws)

        # Clean up dead connections
        if dead_connections:
            async with self._lock:
                for ws in dead_connections:
                    self._client_subscriptions.pop(ws, None)

    async def broadcast_market_status(self, status: Dict[str, Any]) -> None:
        """Broadcast market status to all connected clients."""
        payload = {"type": "MARKET_STATUS", **status}
        await self._broadcast_all(payload)

    async def broadcast_feed_status(self, status: str, message: str = "") -> None:
        """
        Broadcast feed status change to all clients.
        status: "CONNECTED" | "DISCONNECTED" | "STALE"
        """
        payload = {
            "type":      "FEED_STATUS",
            "status":    status,
            "message":   message,
            "timestamp": _now_iso(),
        }
        logger.info(f"WebSocket: broadcasting FEED_STATUS={status}")
        await self._broadcast_all(payload)

    async def broadcast_stale_warning(self, symbol: str, last_update: str) -> None:
        """Broadcast a stale data warning for a specific symbol."""
        payload = {
            "type":        "STALE_DATA_WARNING",
            "symbol":      symbol,
            "last_update": last_update,
            "message":     f"Data for {symbol} has not been updated. Feed may be delayed or disconnected.",
            "timestamp":   _now_iso(),
        }
        await self._broadcast_all(payload)

    async def _broadcast_all(self, payload: Dict[str, Any]) -> None:
        """Send a message to all connected clients."""
        if not self._client_subscriptions:
            return
        dead = set()
        async with self._lock:
            for ws in list(self._client_subscriptions.keys()):
                if not await self._safe_send(ws, payload):
                    dead.add(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._client_subscriptions.pop(ws, None)

    async def _safe_send(self, websocket: WebSocket, data: Dict[str, Any]) -> bool:
        """Send JSON data to a WebSocket. Returns False if send failed."""
        try:
            await websocket.send_json(data)
            return True
        except Exception:
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Return WebSocket manager statistics."""
        return {
            "active_clients": len(self._client_subscriptions),
            "subscriptions": {
                str(id(ws)): list(subs)
                for ws, subs in self._client_subscriptions.items()
            },
        }


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# Module-level singleton
_ws_manager = WebSocketMarketStreamManager()


def get_websocket_manager() -> WebSocketMarketStreamManager:
    return _ws_manager
