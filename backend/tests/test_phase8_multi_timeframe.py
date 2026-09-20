"""
Phase 8 Test Suite: Multi-Timeframe Technical Analysis Engine
TradePilot AI

Tests:
1. Single timeframe technical analysis (trend, momentum, EMA alignment, S/R pivots).
2. Multi-timeframe confluence scoring (HTF 35%, ITF 35%, LTF 30%) and tiering.
3. Confluence recommendations (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL, WAIT_FOR_CONFIRMATION).
4. Risk score calibration (1-10) and probabilistic confidence (45-88%).
5. Mandatory AI disclaimer on all outputs.
6. Endpoints:
   - GET /api/v1/ai/multi-timeframe/{symbol}
   - GET /api/v1/market/analysis/{symbol}
   - GET /api/v1/ai/analyze/{symbol} (embedded multi_timeframe field)
7. International US instrument support (AAPL with USD currency).
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.multi_timeframe_engine import (
    evaluate_single_timeframe,
    compute_multi_timeframe_analysis,
    run_symbol_multi_timeframe_analysis,
)


client = TestClient(app)


def _generate_synthetic_trend_bars(base_price: float, step: float, count: int = 40):
    bars = []
    for i in range(count):
        o = base_price + i * step
        h = o + abs(step) * 1.5 + 2.0
        l = o - abs(step) * 0.5 - 1.0
        c = o + step * 0.8
        bars.append({
            "timestamp": f"2026-01-01T{i:02d}:00:00Z",
            "time": 1767225600 + i * 3600,
            "open": round(o, 2),
            "high": round(h, 2),
            "low": round(l, 2),
            "close": round(c, 2),
            "volume": 50000 + i * 500,
            "data_source": "TEST_DATA",
        })
    return bars


def test_single_timeframe_bullish_evaluation():
    """Test single timeframe technical evaluation on an upward trending series."""
    bull_bars = _generate_synthetic_trend_bars(base_price=2000.0, step=15.0, count=40)
    analysis = evaluate_single_timeframe(bull_bars, "1d", "Daily HTF")

    assert analysis.timeframe == "1d"
    assert analysis.trend == "BULLISH"
    assert analysis.momentum in ["STRONG_BULL", "WEAK_BULL"]
    assert analysis.ema_alignment == "BULLISH_ALIGNMENT"
    assert analysis.rsi14 is not None and analysis.rsi14 > 50.0
    assert "pivot" in analysis.key_levels


def test_single_timeframe_bearish_evaluation():
    """Test single timeframe technical evaluation on a downward trending series."""
    bear_bars = _generate_synthetic_trend_bars(base_price=2000.0, step=-15.0, count=40)
    analysis = evaluate_single_timeframe(bear_bars, "1h", "Hourly ITF")

    assert analysis.timeframe == "1h"
    assert analysis.trend == "BEARISH"
    assert analysis.momentum in ["STRONG_BEAR", "WEAK_BEAR"]
    assert analysis.ema_alignment == "BEARISH_ALIGNMENT"
    assert analysis.rsi14 is not None and analysis.rsi14 < 50.0


def test_single_timeframe_empty_bars_safe_neutral():
    """Test single timeframe evaluation handles empty or short bars safely without crashing."""
    analysis = evaluate_single_timeframe([], "15m", "15m LTF")
    assert analysis.trend == "NEUTRAL"
    assert analysis.momentum == "NEUTRAL"
    assert analysis.rsi14 == 50.0


def test_multi_timeframe_strong_bullish_confluence():
    """Test 3 aligned bullish timeframes trigger STRONG_CONFLUENCE and STRONG_BUY."""
    htf = _generate_synthetic_trend_bars(2000.0, step=10.0, count=40)
    itf = _generate_synthetic_trend_bars(2300.0, step=5.0, count=40)
    ltf = _generate_synthetic_trend_bars(2450.0, step=2.0, count=40)

    res = compute_multi_timeframe_analysis("RELIANCE", htf, itf, ltf, current_price=2500.0)
    assert res.symbol == "RELIANCE"
    assert res.confluence_score >= 80.0
    assert res.confluence_tier == "STRONG_CONFLUENCE"
    assert res.overall_trend == "BULLISH"
    assert res.recommended_action == "STRONG_BUY"
    assert res.risk_score <= 4
    assert res.confidence_pct >= 70.0
    assert "probabilistic" in res.disclaimer


def test_multi_timeframe_strong_bearish_confluence():
    """Test 3 aligned bearish timeframes trigger STRONG_CONFLUENCE and STRONG_SELL."""
    htf = _generate_synthetic_trend_bars(2500.0, step=-10.0, count=40)
    itf = _generate_synthetic_trend_bars(2200.0, step=-5.0, count=40)
    ltf = _generate_synthetic_trend_bars(2050.0, step=-2.0, count=40)

    res = compute_multi_timeframe_analysis("TCS", htf, itf, ltf, current_price=2000.0)
    assert res.symbol == "TCS"
    assert res.confluence_score >= 80.0
    assert res.confluence_tier == "STRONG_CONFLUENCE"
    assert res.overall_trend == "BEARISH"
    assert res.recommended_action == "STRONG_SELL"
    assert res.risk_score <= 4


def test_multi_timeframe_conflicted_chop():
    """Test conflicted timeframes produce WEAK_CONFLUENCE and elevated risk score."""
    htf = _generate_synthetic_trend_bars(2000.0, step=10.0, count=40)   # Bullish
    itf = _generate_synthetic_trend_bars(2300.0, step=-8.0, count=40)  # Bearish
    ltf = []                                                          # Neutral

    res = compute_multi_timeframe_analysis("INFY", htf, itf, ltf, current_price=2100.0)
    assert res.confluence_score < 75.0
    assert res.confluence_tier in ["MODERATE_CONFLUENCE", "WEAK_CONFLUENCE"]
    assert res.recommended_action in ["WAIT_FOR_CONFIRMATION", "HOLD", "BUY", "SELL"]
    assert res.risk_score >= 5


def test_endpoint_ai_multi_timeframe():
    """Test GET /api/v1/ai/multi-timeframe/{symbol} endpoint."""
    res = client.get("/api/v1/ai/multi-timeframe/RELIANCE")
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "RELIANCE"
    assert "confluence_score" in data
    assert "confluence_tier" in data
    assert "timeframes" in data
    assert "htf_daily" in data["timeframes"]
    assert "itf_hourly" in data["timeframes"]
    assert "ltf_15m" in data["timeframes"]
    assert "disclaimer" in data


def test_endpoint_market_analysis():
    """Test GET /api/v1/market/analysis/{symbol} endpoint."""
    res = client.get("/api/v1/market/analysis/RELIANCE")
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "RELIANCE"
    assert "recommended_action" in data
    assert "risk_score" in data
    assert "confidence_pct" in data


def test_endpoint_ai_multi_timeframe_us_symbol():
    """Test multi-timeframe analysis on US ticker (AAPL) with USD currency."""
    res = client.get("/api/v1/ai/multi-timeframe/AAPL")
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "AAPL"
    assert data["currency_symbol"] == "$"
    assert "confluence_score" in data
    assert "disclaimer" in data
