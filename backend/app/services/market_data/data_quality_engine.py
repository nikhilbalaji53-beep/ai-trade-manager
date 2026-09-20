"""
Market Data Quality & Stale Detection Engine — TradePilot AI

Implements Sections 11, 12, 13, and 15:
  - Real-time tick age monitoring (milliseconds / seconds)
  - Multi-tier staleness evaluation: LIVE, WARNING, STALE, DISCONNECTED
  - Multi-hop latency calculation (provider -> backend -> frontend)
  - Automated pause of AI trade recommendations when feed is STALE or DISCONNECTED
  - Configurable staleness thresholds by provider and instrument
  - High data latency warnings (> 1,200 ms)
"""
import os
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from collections import deque

logger = logging.getLogger(__name__)

# Configurable staleness thresholds (seconds)
DEFAULT_STALE_THRESHOLD_SECONDS = float(os.getenv("STALE_THRESHOLD_SECONDS", "15.0"))
DEFAULT_WARNING_THRESHOLD_SECONDS = float(os.getenv("WARNING_THRESHOLD_SECONDS", "8.0"))
HIGH_LATENCY_THRESHOLD_MS = float(os.getenv("HIGH_LATENCY_THRESHOLD_MS", "1200.0"))


class DataQualityEngine:
    """
    Dedicated Quality & Staleness Engine.
    Tracks ticks across Indian (NSE/BSE) and US (NASDAQ/NYSE) feeds.
    """

    def __init__(self):
        self._symbol_ticks: Dict[str, Dict[str, Any]] = {}
        self._provider_heartbeats: Dict[str, float] = {}
        self._reconnect_counts: Dict[str, int] = {"NSE_YFINANCE": 0, "BSE_YFINANCE": 0, "INTERNATIONAL_YFINANCE": 0}
        self._latency_history: deque = deque(maxlen=60)
        self._ai_recommendations_paused: bool = False
        self._pause_reason: Optional[str] = None
        self._thresholds: Dict[str, float] = {
            "NSE_YFINANCE": DEFAULT_STALE_THRESHOLD_SECONDS,
            "BSE_YFINANCE": DEFAULT_STALE_THRESHOLD_SECONDS,
            "INTERNATIONAL_YFINANCE": DEFAULT_STALE_THRESHOLD_SECONDS,
            "BROKER_API": 3.0,
        }

    def set_threshold(self, provider_or_symbol: str, threshold_seconds: float) -> None:
        """Configure custom staleness threshold for a provider or instrument."""
        self._thresholds[provider_or_symbol.upper()] = float(threshold_seconds)

    def record_tick(
        self,
        symbol: str,
        provider_name: str,
        provider_timestamp: Optional[float] = None,
        latency_ms: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Record an incoming tick and calculate latency & age metrics.
        """
        now = time.time()
        sym_clean = symbol.upper().strip()
        self._provider_heartbeats[provider_name] = now

        prov_ts = provider_timestamp or now
        obs_latency = latency_ms if latency_ms is not None else max(10.0, round((now - prov_ts) * 1000.0, 1))
        self._latency_history.append(obs_latency)

        tick_meta = {
            "symbol": sym_clean,
            "provider": provider_name,
            "last_tick_time": now,
            "last_tick_iso": datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
            "provider_timestamp": prov_ts,
            "server_timestamp": now,
            "latency_ms": obs_latency,
            "is_high_latency": obs_latency > HIGH_LATENCY_THRESHOLD_MS,
        }
        self._symbol_ticks[sym_clean] = tick_meta
        return tick_meta

    def record_reconnect(self, provider_name: str) -> int:
        """Increment and track reconnect counts for auto-reconnect monitoring."""
        cnt = self._reconnect_counts.get(provider_name, 0) + 1
        self._reconnect_counts[provider_name] = cnt
        return cnt

    def evaluate_symbol_quality(self, symbol: str, provider_name: str = "NSE_YFINANCE") -> Dict[str, Any]:
        """
        Evaluate real-time data quality for a specific symbol.
        Returns state: LIVE, WARNING, STALE, DISCONNECTED.
        """
        now = time.time()
        sym_clean = symbol.upper().strip()
        tick_info = self._symbol_ticks.get(sym_clean)

        threshold = self._thresholds.get(sym_clean, self._thresholds.get(provider_name, DEFAULT_STALE_THRESHOLD_SECONDS))
        warning_threshold = threshold * 0.6

        if not tick_info:
            return {
                "symbol": sym_clean,
                "status": "DISCONNECTED",
                "label": "NO DATA FEED",
                "tick_age_seconds": None,
                "tick_age_display": "No recent data",
                "latency_ms": None,
                "is_stale": True,
                "is_live": False,
                "ai_safe": False,
                "warning_message": "Feed not connected or symbol unobserved.",
            }

        age_seconds = round(now - tick_info["last_tick_time"], 2)
        latency = tick_info.get("latency_ms", 50.0)

        # State classification
        if age_seconds <= warning_threshold:
            status = "LIVE"
            label = "● FEED LIVE"
            is_stale = False
            is_live = True
            ai_safe = True
            msg = None
        elif age_seconds <= threshold:
            status = "WARNING"
            label = "⚠ FEED DELAY WARNING"
            is_stale = False
            is_live = True
            ai_safe = True
            msg = f"Data approaching stale threshold ({age_seconds:.1f}s / {threshold:.1f}s)."
        elif age_seconds <= (threshold * 4.0):
            status = "STALE"
            label = "⚠ MARKET DATA STALE"
            is_stale = True
            is_live = False
            ai_safe = False
            msg = f"Data older than threshold ({age_seconds:.1f}s > {threshold:.1f}s). AI trade recommendations PAUSED."
        else:
            status = "DISCONNECTED"
            label = "⚠ FEED DISCONNECTED"
            is_stale = True
            is_live = False
            ai_safe = False
            msg = "Feed connection unavailable or dropped."

        if latency > HIGH_LATENCY_THRESHOLD_MS:
            label = "⚠ HIGH DATA LATENCY"

        return {
            "symbol": sym_clean,
            "status": status,
            "label": label,
            "tick_age_seconds": age_seconds,
            "tick_age_display": f"{age_seconds:.1f}s ago" if age_seconds >= 1.0 else f"{int(age_seconds * 1000)}ms",
            "latency_ms": latency,
            "is_stale": is_stale,
            "is_live": is_live,
            "ai_safe": ai_safe,
            "warning_message": msg,
        }

    def evaluate_global_quality(self, is_market_open: bool = True) -> Dict[str, Any]:
        """
        Evaluate system-wide feed health, latency, and AI safety status.
        """
        now = time.time()
        avg_latency = round(sum(self._latency_history) / max(1, len(self._latency_history)), 1)
        latest_tick_age = None
        if self._symbol_ticks:
            latest_time = max(t["last_tick_time"] for t in self._symbol_ticks.values())
            latest_tick_age = round(now - latest_time, 2)

        # Global stale check
        is_stale = (latest_tick_age is not None and latest_tick_age > DEFAULT_STALE_THRESHOLD_SECONDS)
        is_disconnected = (latest_tick_age is None or latest_tick_age > (DEFAULT_STALE_THRESHOLD_SECONDS * 4.0))

        if is_disconnected:
            data_status = "DISCONNECTED"
            label = "FEED DISCONNECTED"
            self._ai_recommendations_paused = True
            self._pause_reason = "Feed disconnected: no recent market ticks"
        elif is_stale:
            data_status = "STALE"
            label = "⚠ MARKET DATA STALE"
            self._ai_recommendations_paused = True
            self._pause_reason = f"Data stale ({latest_tick_age}s > {DEFAULT_STALE_THRESHOLD_SECONDS}s)"
        elif not is_market_open:
            data_status = "MARKET_CLOSED"
            label = "● MARKET CLOSED"
            self._ai_recommendations_paused = False
            self._pause_reason = "Regular trading session is closed"
        elif avg_latency > HIGH_LATENCY_THRESHOLD_MS:
            data_status = "HIGH_LATENCY"
            label = "⚠ HIGH DATA LATENCY"
            self._ai_recommendations_paused = False
            self._pause_reason = None
        else:
            data_status = "LIVE"
            label = "● LIVE"
            self._ai_recommendations_paused = False
            self._pause_reason = None

        return {
            "data_status": data_status,
            "status_label": label,
            "is_stale": is_stale,
            "ai_recommendations_paused": self._ai_recommendations_paused,
            "ai_pause_reason": self._pause_reason,
            "average_latency_ms": avg_latency,
            "is_high_latency": avg_latency > HIGH_LATENCY_THRESHOLD_MS,
            "latest_tick_age_seconds": latest_tick_age,
            "observed_symbols_count": len(self._symbol_ticks),
            "reconnect_counts": dict(self._reconnect_counts),
            "stale_threshold_seconds": DEFAULT_STALE_THRESHOLD_SECONDS,
            "server_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }


# Singleton instance
_quality_engine = DataQualityEngine()


def get_data_quality_engine() -> DataQualityEngine:
    return _quality_engine
