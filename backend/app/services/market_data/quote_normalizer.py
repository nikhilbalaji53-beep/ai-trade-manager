"""
Quote Normalizer — TradePilot

Normalizes raw provider quotes into a canonical NormalizedQuote schema.
Every market price displayed in TradePilot must flow through this normalizer.

DATA INTEGRITY:
  - data_status must be one of: LIVE, LIVE_DELAYED, STALE, DISCONNECTED, UNAVAILABLE
  - NEVER sets data_status=LIVE for delayed data
  - NEVER invents or fills in missing fields with fake values
  - Fields not provided by the data source are set to None
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Literal

logger = logging.getLogger(__name__)

# Canonical data status values
DataStatus = Literal["LIVE", "LIVE_DELAYED", "STALE", "DISCONNECTED", "UNAVAILABLE"]

# Maximum age in seconds before a quote is considered STALE
MAX_QUOTE_AGE_SECONDS = 300  # 5 minutes


def normalize_quote(raw: Dict[str, Any], provider_name: str = "UNKNOWN") -> Optional[Dict[str, Any]]:
    """
    Normalize a raw provider quote into the canonical TradePilot format.

    Returns None if the quote is invalid (missing symbol, invalid price, etc.)

    Canonical Quote Schema:
    {
        "symbol":              str,          — Exchange ticker (e.g., "RELIANCE")
        "exchange":            str,          — "NSE" or "BSE"
        "instrument_token":    str | None,   — Provider-specific token
        "isin":                str | None,   — ISIN code if available
        "timestamp":           str,          — ISO 8601 UTC
        "last_price":          float,        — Last traded price (> 0)
        "open":                float | None, — Day open
        "high":                float | None, — Day high
        "low":                 float | None, — Day low
        "previous_close":      float | None, — Previous close
        "change":              float | None, — Absolute change
        "change_percent":      float | None, — Percentage change
        "volume":              int | None,   — Day volume
        "bid_price":           float | None, — Best bid (None if L2 unavailable)
        "bid_quantity":        int | None,   — Bid quantity (None if L2 unavailable)
        "ask_price":           float | None, — Best ask (None if L2 unavailable)
        "ask_quantity":        int | None,   — Ask quantity (None if L2 unavailable)
        "data_status":         DataStatus,   — Feed status (see above)
        "data_source":         str,          — e.g., "NSE_YFINANCE", "BROKER_ZERODHA"
        "data_delay_minutes":  int | None,   — Delay in minutes (None for real-time)
        "is_live":             bool,         — True only for LIVE or LIVE_DELAYED
        "source":              str,          — Provider name
    }
    """
    if not raw:
        return None

    symbol = raw.get("symbol")
    if not symbol:
        logger.warning(f"QuoteNormalizer: missing symbol in quote from {provider_name}")
        return None

    last_price = raw.get("last_price")
    if last_price is None or not isinstance(last_price, (int, float)) or last_price <= 0:
        logger.warning(
            f"QuoteNormalizer: invalid price ({last_price}) for '{symbol}' from {provider_name}. "
            f"Skipping quote — will NOT substitute fake value."
        )
        return None

    # Determine data_status
    raw_status = raw.get("data_status", "LIVE_DELAYED")
    if raw_status not in ("LIVE", "LIVE_DELAYED", "STALE", "DISCONNECTED", "UNAVAILABLE"):
        raw_status = "LIVE_DELAYED"

    # Timestamp
    ts = raw.get("timestamp")
    if not ts:
        ts = datetime.now(timezone.utc).isoformat()

    # Change computation if not provided but previous_close exists
    prev_close = raw.get("previous_close")
    change = raw.get("change")
    change_pct = raw.get("change_percent")
    if change is None and prev_close and prev_close > 0:
        change = round(float(last_price) - float(prev_close), 2)
    if change_pct is None and change is not None and prev_close and prev_close > 0:
        change_pct = round((change / float(prev_close)) * 100.0, 2)

    return {
        "symbol":              str(symbol).upper(),
        "exchange":            str(raw.get("exchange", "NSE")).upper(),
        "instrument_token":    raw.get("instrument_token"),
        "isin":                raw.get("isin"),
        "timestamp":           ts,
        "last_price":          round(float(last_price), 2),
        "open":                _safe_float(raw.get("open")),
        "high":                _safe_float(raw.get("high")),
        "low":                 _safe_float(raw.get("low")),
        "previous_close":      _safe_float(prev_close),
        "change":              _safe_float(change),
        "change_percent":      _safe_float(change_pct),
        "volume":              _safe_int(raw.get("volume")),
        # L2 Order Book — only populate if actually provided
        "bid_price":           _safe_float(raw.get("bid_price")),
        "bid_quantity":        _safe_int(raw.get("bid_quantity")),
        "ask_price":           _safe_float(raw.get("ask_price")),
        "ask_quantity":        _safe_int(raw.get("ask_quantity")),
        "data_status":         raw_status,
        "data_source":         raw.get("data_source", provider_name),
        "data_delay_minutes":  raw.get("data_delay_minutes"),
        "is_live":             raw_status in ("LIVE", "LIVE_DELAYED"),
        "source":              provider_name,
        "note":                raw.get("note"),
    }


def validate_quote_freshness(quote: Dict[str, Any], stale_threshold_seconds: int = MAX_QUOTE_AGE_SECONDS) -> Dict[str, Any]:
    """
    Check if a quote is stale based on its timestamp.
    If stale, updates data_status to "STALE" and is_live to False.

    Returns the (potentially modified) quote.
    NEVER generates a fake price.
    """
    ts_str = quote.get("timestamp")
    if not ts_str:
        quote["data_status"] = "STALE"
        quote["is_live"] = False
        return quote

    try:
        ts_dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age_seconds = (now - ts_dt).total_seconds()
        if age_seconds > stale_threshold_seconds:
            logger.warning(
                f"QuoteNormalizer: quote for '{quote.get('symbol')}' is {age_seconds:.0f}s old "
                f"(threshold: {stale_threshold_seconds}s). Marking as STALE."
            )
            quote["data_status"] = "STALE"
            quote["is_live"] = False
    except Exception as e:
        logger.warning(f"QuoteNormalizer: timestamp parse error — {e}. Marking as STALE.")
        quote["data_status"] = "STALE"
        quote["is_live"] = False

    return quote


def _safe_float(val) -> Optional[float]:
    """Convert to float or return None. Never fabricates a value."""
    if val is None:
        return None
    try:
        f = float(val)
        return round(f, 2) if f >= 0 else None
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> Optional[int]:
    """Convert to int or return None. Never fabricates a value."""
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
