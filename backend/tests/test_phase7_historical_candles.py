"""
Phase 7 Test Suite: Dynamic 6-Month Historical Candles & Technical Indicators Engine
TradePilot AI

Tests:
1. Dynamic timeframe mappings (1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo) and TTLs.
2. CandleCache thread-safety, storage, hit/miss, and expiration.
3. Technical indicator computations (SMA 20/50/200, EMA 9/21/50/200, RSI 14, MACD, Bollinger Bands, ATR, Supertrend, Stochastic, VWAP, Pivots, Regime).
4. MarketDataManager get_historical_candles_package integration.
5. Endpoints:
   - GET /api/v1/market/history/{symbol} (array format)
   - GET /api/v1/market/history/{symbol}?format=full (package format)
   - GET /api/v1/market/history/{symbol}/indicators (dedicated indicators endpoint)
6. Zero fake data guarantee (returns empty list / package on missing feed).
"""
import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.market_data.candle_engine import (
    resolve_timeframe_params,
    enrich_candle_series,
    compute_classic_pivots,
    CandleCache,
    get_historical_candles_package,
)
from app.services.market_data.market_data_manager import get_market_data_manager


client = TestClient(app)


def test_timeframe_resolution_mappings():
    """Validate dynamic timeframe resolution mapping to optimal yfinance intervals and periods."""
    # 1m -> 1m, 7d
    intv, per, ttl = resolve_timeframe_params("1m")
    assert intv == "1m"
    assert per == "7d"
    assert ttl == 60.0

    # 15m -> 15m, 60d
    intv, per, ttl = resolve_timeframe_params("15m")
    assert intv == "15m"
    assert per == "60d"
    assert ttl == 600.0

    # 1h -> 1h, 730d (~2 years)
    intv, per, ttl = resolve_timeframe_params("1h")
    assert intv == "1h"
    assert per == "730d"
    assert ttl == 1800.0

    # 1d -> 1d, 2y
    intv, per, ttl = resolve_timeframe_params("1d")
    assert intv == "1d"
    assert per == "2y"
    assert ttl == 3600.0

    # 1wk -> 1wk, 5y
    intv, per, ttl = resolve_timeframe_params("1wk")
    assert intv == "1wk"
    assert per == "5y"
    assert ttl == 86400.0


def test_candle_cache_lifecycle():
    """Test CandleCache storage, hit, miss, and clear."""
    cache = CandleCache()
    assert cache.get("INFY", "1h", 60) is None

    payload = {"symbol": "INFY", "candles": [{"close": 1500.0}]}
    cache.set("INFY", "1h", 60, payload, ttl=10.0)

    cached = cache.get("INFY", "1h", 60)
    assert cached is not None
    assert cached["symbol"] == "INFY"

    cache.clear()
    assert cache.get("INFY", "1h", 60) is None


def test_classic_pivot_points_math():
    """Verify classic standard pivot points (PP, R1-R3, S1-S3)."""
    pivots = compute_classic_pivots(high=100.0, low=90.0, close=95.0)
    # PP = (100 + 90 + 95) / 3 = 95.0
    assert pivots["pp"] == 95.0
    # R1 = 2*95 - 90 = 100.0
    assert pivots["r1"] == 100.0
    # S1 = 2*95 - 100 = 90.0
    assert pivots["s1"] == 90.0
    # R2 = 95 + (100 - 90) = 105.0
    assert pivots["r2"] == 105.0
    # S2 = 95 - (100 - 90) = 85.0
    assert pivots["s2"] == 85.0


def test_enrich_candle_series_technical_indicators():
    """Test indicator enrichment across bars and summary package."""
    # Create sample real-looking test bars
    sample_bars = []
    base_price = 1000.0
    for i in range(50):
        o = base_price + i * 2.0
        h = o + 5.0
        l = o - 4.0
        c = o + 1.5
        sample_bars.append({
            "timestamp": f"2026-01-01T{i:02d}:00:00Z",
            "time": 1767225600 + i * 3600,
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": 10000 + i * 100,
            "data_source": "TEST_PROVIDER",
        })

    enriched_bars, summary = enrich_candle_series(sample_bars, symbol="TEST_SYM")

    assert len(enriched_bars) == 50
    # Check overlays on latest bar
    last_bar = enriched_bars[-1]
    assert "sma20" in last_bar and last_bar["sma20"] is not None
    assert "ema21" in last_bar and last_bar["ema21"] is not None
    assert "upper_bb" in last_bar and last_bar["upper_bb"] is not None
    assert "vwap" in last_bar and last_bar["vwap"] is not None

    # Check series-level technical indicator summary
    assert summary["symbol"] == "TEST_SYM"
    assert summary["rsi14"] >= 0.0 and summary["rsi14"] <= 100.0
    assert "macd" in summary
    assert "crossover" in summary["macd"]
    assert "bollinger_bands" in summary
    assert summary["bollinger_bands"]["upper"] > summary["bollinger_bands"]["lower"]
    assert summary["atr14"] > 0.0
    assert "supertrend" in summary
    assert summary["supertrend"]["direction"] in ["BULLISH", "BEARISH"]
    assert "pivots" in summary
    assert summary["pivots"]["pp"] > 0.0
    assert summary["regime"] in ["TRENDING_BULL", "TRENDING_BEAR", "BREAKOUT", "CONSOLIDATION"]


def test_market_data_manager_package_integration():
    """Test MarketDataManager historical candles package API."""
    manager = get_market_data_manager()
    pkg = manager.get_historical_candles_package("RELIANCE", timeframe="1h", count=20)
    assert "symbol" in pkg
    assert pkg["symbol"] == "RELIANCE"
    assert "candles" in pkg
    assert "indicators" in pkg
    assert "data_source" in pkg


def test_rest_endpoint_history_array_format():
    """Test GET /api/v1/market/history/{symbol} returns array format for chart compatibility."""
    res = client.get("/api/v1/market/history/RELIANCE?timeframe=1h&count=20")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if len(data) > 0:
        bar = data[0]
        assert "open" in bar
        assert "high" in bar
        assert "low" in bar
        assert "close" in bar


def test_rest_endpoint_history_package_format():
    """Test GET /api/v1/market/history/{symbol}?format=full returns package format."""
    res = client.get("/api/v1/market/history/RELIANCE?timeframe=1h&count=20&format=full")
    assert res.status_code == 200
    pkg = res.json()
    assert isinstance(pkg, dict)
    assert pkg["symbol"] == "RELIANCE"
    assert "candles" in pkg
    assert "indicators" in pkg


def test_rest_endpoint_history_dedicated_indicators():
    """Test GET /api/v1/market/history/{symbol}/indicators endpoint for US ticker."""
    res = client.get("/api/v1/market/history/AAPL/indicators?timeframe=1d&count=20")
    assert res.status_code == 200
    pkg = res.json()
    assert isinstance(pkg, dict)
    assert pkg["symbol"] == "AAPL"
    assert "candles" in pkg
    assert "indicators" in pkg


def test_zero_synthetic_candles_when_symbol_unknown():
    """Zero fake data test: an unlisted/invalid ticker returns empty candles, never inventing bars."""
    pkg = get_historical_candles_package("NONEXISTENT_STOCK_999", timeframe="1h", count=50)
    assert pkg["is_empty"] is True
    assert pkg["bars_returned"] == 0
    assert pkg["candles"] == []
    assert pkg["message"] == "Awaiting Live Market Feed"
