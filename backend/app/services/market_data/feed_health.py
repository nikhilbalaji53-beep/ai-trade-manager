"""
Feed Health Monitor — TradePilot

Tracks the health of the active market data feed.
Exposes metrics for the /api/v1/market/feed-health endpoint.

Metrics tracked:
  - provider_name       — Which provider is active
  - connection_status   — LIVE / DELAYED / STALE / DISCONNECTED
  - last_tick_time      — When the last valid quote was received
  - ticks_per_minute    — Rate of incoming quotes
  - rejected_ticks      — Quotes rejected due to invalid price/timestamp
  - stale_ticks         — Quotes that were returned from cache as stale
  - subscription_count  — Number of symbols subscribed
  - provider_latency_ms — Round-trip latency for last fetch
"""
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from collections import deque

logger = logging.getLogger(__name__)


class FeedHealthMonitor:
    """
    Tracks real-time health metrics for the active market data feed.
    Thread-safe for concurrent access from background streaming task.
    """

    def __init__(self):
        self._provider_name: str = "NOT_INITIALIZED"
        self._last_tick_time: Optional[float] = None
        self._last_tick_symbol: Optional[str] = None
        self._tick_timestamps: deque = deque(maxlen=60)  # last 60 tick timestamps
        self._rejected_ticks: int = 0
        self._stale_ticks: int = 0
        self._subscription_count: int = 0
        self._last_latency_ms: Optional[float] = None
        self._error_log: deque = deque(maxlen=20)

    def record_tick(self, symbol: str, latency_ms: Optional[float] = None) -> None:
        """Record a successful tick receipt."""
        now = time.time()
        self._last_tick_time = now
        self._last_tick_symbol = symbol
        self._tick_timestamps.append(now)
        if latency_ms is not None:
            self._last_latency_ms = round(latency_ms, 2)

    def record_rejected_tick(self, symbol: str, reason: str) -> None:
        """Record a tick that was rejected (invalid price, bad timestamp, etc.)."""
        self._rejected_ticks += 1
        self._error_log.append({
            "time": datetime.now(timezone.utc).isoformat(),
            "type": "REJECTED_TICK",
            "symbol": symbol,
            "reason": reason,
        })
        logger.warning(f"FeedHealthMonitor: rejected tick for '{symbol}': {reason}")

    def record_stale_tick(self, symbol: str) -> None:
        """Record a tick that was served from stale cache."""
        self._stale_ticks += 1
        logger.debug(f"FeedHealthMonitor: stale tick served for '{symbol}'")

    def set_provider(self, provider_name: str) -> None:
        self._provider_name = provider_name

    def set_subscription_count(self, count: int) -> None:
        self._subscription_count = count

    def get_connection_status(self, is_provider_connected: bool) -> str:
        """
        Determine the feed connection status label.

        LIVE          — provider connected and ticks arriving within 5 minutes
        LIVE_DELAYED  — provider connected but delay > 60 seconds (yfinance)
        STALE         — provider connected but no tick in > 5 minutes
        DISCONNECTED  — provider not connected
        """
        if not is_provider_connected:
            return "DISCONNECTED"

        if self._last_tick_time is None:
            return "AWAITING_FIRST_TICK"

        age_seconds = time.time() - self._last_tick_time
        if age_seconds < 60:
            return "LIVE_DELAYED"  # yfinance is always delayed, never truly LIVE
        elif age_seconds < 300:
            return "STALE"
        else:
            return "DISCONNECTED"

    def get_ticks_per_minute(self) -> float:
        """Compute tick rate over the last 60 seconds."""
        if not self._tick_timestamps:
            return 0.0
        now = time.time()
        recent = [ts for ts in self._tick_timestamps if now - ts <= 60.0]
        return round(len(recent), 1)

    def get_health_metrics(self, is_provider_connected: bool = True) -> Dict[str, Any]:
        """Return all feed health metrics for the health endpoint."""
        now = time.time()
        last_tick_age = None
        last_tick_iso = None
        if self._last_tick_time:
            last_tick_age = round(now - self._last_tick_time, 1)
            last_tick_iso = datetime.fromtimestamp(self._last_tick_time, tz=timezone.utc).isoformat()

        return {
            "provider_name":        self._provider_name,
            "connection_status":    self.get_connection_status(is_provider_connected),
            "is_connected":         is_provider_connected,
            "last_tick_time":       last_tick_iso,
            "last_tick_age_seconds": last_tick_age,
            "last_tick_symbol":     self._last_tick_symbol,
            "ticks_per_minute":     self.get_ticks_per_minute(),
            "rejected_ticks_total": self._rejected_ticks,
            "stale_ticks_total":    self._stale_ticks,
            "subscription_count":   self._subscription_count,
            "last_latency_ms":      self._last_latency_ms,
            "recent_errors":        list(self._error_log)[-5:],
            "data_delay_minutes":   15,  # Yahoo Finance inherent delay
            "note":                 (
                "ticks_per_minute reflects the rate of quote fetches from Yahoo Finance. "
                "This is NOT a real-time tick rate. For true real-time metrics, "
                "configure MARKET_DATA_PROVIDER=BROKER_API."
            ),
            "timestamp":            datetime.now(timezone.utc).isoformat(),
        }


# Module-level singleton
_feed_health = FeedHealthMonitor()


def get_feed_health_monitor() -> FeedHealthMonitor:
    return _feed_health
