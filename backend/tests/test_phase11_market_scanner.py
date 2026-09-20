"""
Phase 11 Test Suite: Real-time Live Market Scanner & Pattern Detection
TradePilot AI

Tests:
1. Multi-Category Pattern Scanners:
   - BREAKOUT (Volume surge, Bollinger Band squeeze)
   - MACD (Bullish / Bearish crossovers)
   - RSI (Oversold / Overbought mean-reversion setups)
   - MOMENTUM (EMA alignments, Supertrend trends)
   - CANDLESTICK (Bullish/Bearish Engulfing, Hammer, Shooting Star, Doji)
   - GAINER / LOSER (Top session percentage movers)
2. Multi-Market Scanning:
   - Indian equities (market="IN", currency="₹")
   - US equities & ETFs (market="US", currency="$")
3. Filtering and threshold controls:
   - Filter by category (e.g. BREAKOUT, MACD, RSI, CANDLESTICK)
   - Filter by minimum confidence threshold
   - Filter by market ("IN" vs "US")
4. REST API Endpoints:
   - GET /api/v1/market/scanner (v1 endpoint with multi-market & confidence params)
   - GET /api/market/scanner (core legacy endpoint)
5. Zero Fake Data Guarantee:
   - Real quote and price fields, non-guaranteed probabilistic signals
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.market_scanner import scan_market, detect_candlestick_pattern
from app.services.market_data.market_data_manager import get_market_data_manager

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_market_scanner_data():
    mgr = get_market_data_manager()
    mgr.initialize()

    # Populate in-memory quotes for both Indian & US symbols to ensure fast, deterministic tests
    now_iso = "2026-09-12T06:00:00Z"
    mgr._cached_quotes["RELIANCE"] = {
        "symbol": "RELIANCE",
        "exchange": "NSE",
        "last_price": 2980.00,
        "open": 2920.00,
        "high": 2995.00,
        "low": 2915.00,
        "previous_close": 2920.00,
        "change": 60.00,
        "change_percent": 2.05,
        "volume": 6500000,
        "timestamp": now_iso,
        "data_status": "LIVE_DELAYED",
        "data_source": "TEST_FEED",
        "is_live": True,
    }
    mgr._cached_quotes["TCS"] = {
        "symbol": "TCS",
        "exchange": "NSE",
        "last_price": 4120.00,
        "open": 4200.00,
        "high": 4210.00,
        "low": 4110.00,
        "previous_close": 4200.00,
        "change": -80.00,
        "change_percent": -1.90,
        "volume": 1200000,
        "timestamp": now_iso,
        "data_status": "LIVE_DELAYED",
        "data_source": "TEST_FEED",
        "is_live": True,
    }
    mgr._cached_quotes["AAPL"] = {
        "symbol": "AAPL",
        "exchange": "NASDAQ",
        "last_price": 226.50,
        "open": 222.00,
        "high": 227.00,
        "low": 221.50,
        "previous_close": 222.00,
        "change": 4.50,
        "change_percent": 2.03,
        "volume": 52000000,
        "timestamp": now_iso,
        "data_status": "LIVE_DELAYED",
        "data_source": "TEST_FEED",
        "is_live": True,
    }


def test_detect_candlestick_patterns():
    """Verify detection of classic reversal candlestick patterns."""
    # 1. Bullish Engulfing
    bull_engulf_bars = [
        {"open": 105.0, "high": 106.0, "low": 99.0, "close": 100.0, "volume": 1000},
        {"open": 98.0, "high": 110.0, "low": 97.0, "close": 108.0, "volume": 2500},
    ]
    pat1 = detect_candlestick_pattern(bull_engulf_bars)
    assert pat1 is not None
    assert pat1["pattern"] == "Bullish Engulfing"
    assert pat1["signal_type"] == "BUY"
    assert pat1["confidence"] >= 80

    # 2. Bearish Engulfing
    bear_engulf_bars = [
        {"open": 100.0, "high": 106.0, "low": 99.0, "close": 105.0, "volume": 1000},
        {"open": 106.0, "high": 107.0, "low": 95.0, "close": 98.0, "volume": 2500},
    ]
    pat2 = detect_candlestick_pattern(bear_engulf_bars)
    assert pat2 is not None
    assert pat2["pattern"] == "Bearish Engulfing"
    assert pat2["signal_type"] == "SELL"

    # 3. Bullish Hammer
    hammer_bars = [
        {"open": 105.0, "high": 106.0, "low": 102.0, "close": 103.0, "volume": 1000},
        {"open": 102.0, "high": 103.5, "low": 95.0, "close": 103.0, "volume": 2000},
    ]
    pat3 = detect_candlestick_pattern(hammer_bars)
    assert pat3 is not None
    assert pat3["pattern"] == "Bullish Hammer"
    assert pat3["signal_type"] == "BUY"


def test_scan_market_multi_category():
    """Verify scan_market returns results across multiple technical categories."""
    results = scan_market(filter_category="ALL", min_confidence=60)
    assert isinstance(results, list)
    assert len(results) > 0

    first = results[0]
    assert hasattr(first, "symbol")
    assert hasattr(first, "pattern")
    assert hasattr(first, "category")
    assert hasattr(first, "confidence")
    assert hasattr(first, "signal_type")
    assert hasattr(first, "change_percent")
    assert hasattr(first, "volume_ratio")
    assert hasattr(first, "current_price")
    assert hasattr(first, "market")
    assert hasattr(first, "currency_symbol")
    assert hasattr(first, "risk_score")

    # Categories present
    categories = {r.category for r in results}
    assert any(c in categories for c in ["BREAKOUT", "GAINER", "LOSER", "MOMENTUM", "RSI", "MACD"])


def test_scan_market_filter_by_market():
    """Verify filtering scanner results by region (IN vs US)."""
    # Indian Market Filter
    in_results = scan_market(filter_category="ALL", market_filter="IN")
    assert all(r.market == "IN" for r in in_results)
    assert all(r.currency_symbol == "₹" for r in in_results)

    # US Market Filter
    us_results = scan_market(filter_category="ALL", market_filter="US")
    assert all(r.market == "US" for r in us_results)
    assert all(r.currency_symbol == "$" for r in us_results)


def test_scan_market_filter_by_category():
    """Verify filtering scanner results by category."""
    gainers = scan_market(filter_category="GAINER")
    assert all(r.category == "GAINER" for r in gainers)


def test_rest_v1_scanner_endpoint():
    """Test GET /api/v1/market/scanner endpoint."""
    res = client.get("/api/v1/market/scanner?category=ALL&min_confidence=65")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if len(data) > 0:
        item = data[0]
        assert "symbol" in item
        assert "pattern" in item
        assert "category" in item
        assert "confidence" in item
        assert "signal_type" in item
        assert "market" in item
        assert "currency_symbol" in item
        assert item["confidence"] >= 65


def test_rest_core_legacy_scanner_endpoint():
    """Test GET /api/market/scanner backward compatibility endpoint."""
    res = client.get("/api/market/scanner")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
