"""
Historical Candle & Multi-Timeframe Technical Indicator Engine — TradePilot AI

Implements Phase 7:
  - Dynamic 6-month historical candles up to multi-year history
  - Dynamic timeframe mapping for yfinance / broker APIs:
      1m:  7d max
      5m:  60d max
      15m: 60d max
      30m: 60d max
      1h:  730d max (~2 years)
      1d:  6mo - 2y (up to 5y)
      1wk: multi-year (5y)
      1mo: multi-year (10y)
  - Full technical indicators on bars and series:
      SMA (20, 50, 200), EMA (9, 21, 50, 200)
      RSI (14-period standard)
      MACD (12, 26, 9)
      Bollinger Bands (20, 2.0 std dev)
      ATR (14-period)
      Supertrend (10, 3.0)
      Stochastic Oscillator (14, 3)
      VWAP (Volume-Weighted Average Price)
      Classic Pivot Points (PP, R1, R2, R3, S1, S2, S3)
      Market Regime classification
  - Thread-safe in-memory caching with timeframe-based TTL
  - Strict Data Integrity: NEVER produces mock or synthetic candles when feed is down
"""
import time
import math
import logging
import threading
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone

from app.services.feature_engineering import (
    compute_sma,
    compute_ema,
    compute_rsi,
    compute_macd,
    compute_bollinger_bands,
    compute_atr,
    compute_supertrend,
    compute_stochastic,
    compute_vwap,
    compute_obv,
)

logger = logging.getLogger(__name__)

# Timeframe configuration with optimal yfinance interval, period, and cache TTL
TIMEFRAME_CONFIGS: Dict[str, Dict[str, Any]] = {
    "1m":  {"interval": "1m",  "period": "7d",   "ttl": 60.0},
    "3m":  {"interval": "5m",  "period": "60d",  "ttl": 120.0},
    "5m":  {"interval": "5m",  "period": "60d",  "ttl": 300.0},
    "15m": {"interval": "15m", "period": "60d",  "ttl": 600.0},
    "30m": {"interval": "30m", "period": "60d",  "ttl": 900.0},
    "1h":  {"interval": "1h",  "period": "730d", "ttl": 1800.0},
    "2h":  {"interval": "1h",  "period": "730d", "ttl": 1800.0},
    "4h":  {"interval": "1h",  "period": "730d", "ttl": 1800.0},
    "1d":  {"interval": "1d",  "period": "2y",   "ttl": 3600.0},
    "1D":  {"interval": "1d",  "period": "2y",   "ttl": 3600.0},
    "1w":  {"interval": "1wk", "period": "5y",   "ttl": 86400.0},
    "1wk": {"interval": "1wk", "period": "5y",   "ttl": 86400.0},
    "1W":  {"interval": "1wk", "period": "5y",   "ttl": 86400.0},
    "1mo": {"interval": "1mo", "period": "5y",   "ttl": 86400.0},
    "1M":  {"interval": "1mo", "period": "5y",   "ttl": 86400.0},
    "6mo": {"interval": "1d",  "period": "6mo",  "ttl": 3600.0},
    "6M":  {"interval": "1d",  "period": "6mo",  "ttl": 3600.0},
    "past_6mo": {"interval": "1d", "period": "6mo", "ttl": 3600.0},
    "1y":  {"interval": "1d",  "period": "1y",    "ttl": 3600.0},
    "1Y":  {"interval": "1d",  "period": "1y",    "ttl": 3600.0},
}


class CandleCache:
    """Thread-safe in-memory cache for historical candle series."""

    def __init__(self):
        self._cache: Dict[Tuple[str, str, int], Tuple[float, Dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def get(self, symbol: str, timeframe: str, count: int) -> Optional[Dict[str, Any]]:
        key = (symbol.upper().strip(), timeframe.lower().strip(), count)
        now = time.time()
        with self._lock:
            if key in self._cache:
                exp, data = self._cache[key]
                if now < exp:
                    return data
                else:
                    del self._cache[key]
        return None

    def set(self, symbol: str, timeframe: str, count: int, data: Dict[str, Any], ttl: float) -> None:
        key = (symbol.upper().strip(), timeframe.lower().strip(), count)
        now = time.time()
        with self._lock:
            self._cache[key] = (now + ttl, data)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


_candle_cache = CandleCache()


def get_candle_cache() -> CandleCache:
    return _candle_cache


def resolve_timeframe_params(timeframe: str) -> Tuple[str, str, float]:
    """
    Resolve interval, historical period, and cache TTL for a timeframe.
    """
    cfg = TIMEFRAME_CONFIGS.get(timeframe.strip())
    if not cfg:
        # Check normalized lowercase
        cfg = TIMEFRAME_CONFIGS.get(timeframe.lower().strip(), TIMEFRAME_CONFIGS["1h"])
    return cfg["interval"], cfg["period"], cfg["ttl"]


def compute_classic_pivots(high: float, low: float, close: float) -> Dict[str, float]:
    """
    Compute Classic Standard Pivot Points (PP, R1-R3, S1-S3).
    """
    pp = round((high + low + close) / 3.0, 2)
    diff = high - low
    r1 = round((2.0 * pp) - low, 2)
    s1 = round((2.0 * pp) - high, 2)
    r2 = round(pp + diff, 2)
    s2 = round(pp - diff, 2)
    r3 = round(high + 2.0 * (pp - low), 2)
    s3 = round(low - 2.0 * (high - pp), 2)
    return {
        "pp": pp,
        "r1": r1,
        "r2": r2,
        "r3": r3,
        "s1": s1,
        "s2": s2,
        "s3": s3,
    }


def enrich_candle_series(bars: List[Dict[str, Any]], symbol: str = "") -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Enrich raw OHLCV bars with technical indicators on both per-bar and series level.
    Returns: (enriched_bars, indicators_summary)
    """
    if not bars:
        return [], {
            "status": "EMPTY",
            "message": "Awaiting Live Market Feed",
            "symbol": symbol,
        }

    closes = [float(b["close"]) for b in bars]
    highs = [float(b["high"]) for b in bars]
    lows = [float(b["low"]) for b in bars]
    volumes = [float(b.get("volume", 0)) for b in bars]

    n = len(bars)
    sma20 = compute_sma(closes, min(20, n))
    sma50 = compute_sma(closes, min(50, n))
    sma200 = compute_sma(closes, min(200, n))

    ema9 = compute_ema(closes, min(9, n))
    ema21 = compute_ema(closes, min(21, n))
    ema50 = compute_ema(closes, min(50, n))
    ema200 = compute_ema(closes, min(200, n))

    # Enrich each individual bar for charting overlays
    enriched = []
    for i, b in enumerate(bars):
        c = b.copy()
        c["sma20"] = round(sma20[i], 2) if i < len(sma20) else None
        c["sma50"] = round(sma50[i], 2) if i < len(sma50) else None
        c["ema9"] = round(ema9[i], 2) if i < len(ema9) else None
        c["ema21"] = round(ema21[i], 2) if i < len(ema21) else None

        sub_closes = closes[: i + 1]
        if len(sub_closes) >= 2:
            up, mid, low, _, _ = compute_bollinger_bands(sub_closes, min(20, len(sub_closes)), 2.0)
            c["upper_bb"] = up
            c["mid_bb"] = mid
            c["lower_bb"] = low
        else:
            c["upper_bb"] = None
            c["mid_bb"] = None
            c["lower_bb"] = None

        # VWAP approximation on bar
        h = float(b.get("high", b["close"]))
        l = float(b.get("low", b["close"]))
        c["vwap"] = round((h + l + float(b["close"])) / 3.0, 2)
        enriched.append(c)

    # Compute series-level full technical summary
    rsi = compute_rsi(closes, 14)
    macd_line, macd_sig, macd_h, macd_cross = compute_macd(closes, 12, 26, 9)
    bb_up, bb_mid, bb_low, bb_pct_b, bb_bw = compute_bollinger_bands(closes, 20, 2.0)
    atr = compute_atr(highs, lows, closes, 14)
    st_val, st_dir = compute_supertrend(highs, lows, closes, 10, 3.0)
    stoch_k, stoch_d = compute_stochastic(highs, lows, closes, 14, 3)
    vwap_val = compute_vwap(highs, lows, closes, volumes)
    obv_val = compute_obv(closes, volumes)

    # Classic Pivots from recent range
    recent_len = min(n, 20)
    p_high = max(highs[-recent_len:]) if highs else closes[-1]
    p_low = min(lows[-recent_len:]) if lows else closes[-1]
    p_close = closes[-1]
    pivots = compute_classic_pivots(p_high, p_low, p_close)

    # Market regime classification
    curr_price = closes[-1]
    last_sma50 = sma50[-1] if sma50 else curr_price
    last_ema21 = ema21[-1] if ema21 else curr_price

    if curr_price > last_sma50 and last_ema21 > last_sma50 and rsi > 55:
        regime = "TRENDING_BULL"
    elif curr_price < last_sma50 and last_ema21 < last_sma50 and rsi < 45:
        regime = "TRENDING_BEAR"
    elif bb_bw > 10.0 and abs(bb_pct_b - 0.5) > 0.35:
        regime = "BREAKOUT"
    else:
        regime = "CONSOLIDATION"

    summary = {
        "symbol": symbol,
        "last_close": curr_price,
        "sma20": round(sma20[-1], 2) if sma20 else None,
        "sma50": round(sma50[-1], 2) if sma50 else None,
        "sma200": round(sma200[-1], 2) if sma200 else None,
        "ema9": round(ema9[-1], 2) if ema9 else None,
        "ema21": round(ema21[-1], 2) if ema21 else None,
        "ema50": round(ema50[-1], 2) if ema50 else None,
        "ema200": round(ema200[-1], 2) if ema200 else None,
        "rsi14": rsi,
        "rsi_condition": "OVERBOUGHT" if rsi > 70 else "OVERSOLD" if rsi < 30 else "NEUTRAL",
        "macd": {
            "macd": macd_line,
            "signal": macd_sig,
            "hist": macd_h,
            "crossover": macd_cross,
        },
        "bollinger_bands": {
            "upper": bb_up,
            "middle": bb_mid,
            "lower": bb_low,
            "bandwidth": bb_bw,
            "pct_b": bb_pct_b,
        },
        "atr14": atr,
        "supertrend": {
            "value": st_val,
            "direction": st_dir,
        },
        "stochastic": {
            "k": stoch_k,
            "d": stoch_d,
        },
        "vwap": vwap_val,
        "obv": obv_val,
        "pivots": pivots,
        "regime": regime,
        "bars_evaluated": n,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    return enriched, summary


def get_historical_candles_package(
    symbol: str,
    timeframe: str = "1h",
    count: int = 100,
    manager: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Primary engine entry point: fetches dynamic real historical candles,
    checks the in-memory cache, enriches with full technical indicators,
    and returns the standardized payload package.
    """
    clean_sym = symbol.upper().strip()
    norm_tf = timeframe.strip()
    cache = get_candle_cache()

    # Check cache
    cached_pkg = cache.get(clean_sym, norm_tf, count)
    if cached_pkg is not None:
        return cached_pkg

    # If manager not passed, retrieve singleton
    if manager is None:
        from app.services.market_data.market_data_manager import get_market_data_manager
        manager = get_market_data_manager()

    _, _, ttl = resolve_timeframe_params(norm_tf)

    # Fetch raw bars from market data manager
    raw_bars = manager.get_historical_candles(clean_sym, timeframe=norm_tf, count=count)

    if not raw_bars:
        empty_pkg = {
            "symbol": clean_sym,
            "timeframe": norm_tf,
            "count": count,
            "bars_returned": 0,
            "data_source": "FEED_UNAVAILABLE",
            "is_empty": True,
            "message": "Awaiting Live Market Feed",
            "candles": [],
            "indicators": {},
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        return empty_pkg

    # Enrich with technical indicators
    enriched_bars, indicators_summary = enrich_candle_series(raw_bars, symbol=clean_sym)

    package = {
        "symbol": clean_sym,
        "timeframe": norm_tf,
        "count": count,
        "bars_returned": len(enriched_bars),
        "data_source": raw_bars[0].get("data_source", "ACTIVE_PROVIDER"),
        "is_empty": False,
        "message": "OK",
        "candles": enriched_bars,
        "indicators": indicators_summary,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    # Store in cache
    cache.set(clean_sym, norm_tf, count, package, ttl)
    return package
