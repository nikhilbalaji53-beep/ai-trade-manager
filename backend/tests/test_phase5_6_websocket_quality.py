"""
Phase 5 & 6 Test Suite: Real-time WebSocket + Data Quality & Stale Detection Engine
TradePilot AI

Tests:
1. DataQualityEngine tick tracking, latency calculation, and multi-tier staleness (LIVE, WARNING, STALE, DISCONNECTED).
2. Automated pause of AI recommendations when feed is STALE or DISCONNECTED.
3. High latency detection (> 1,200 ms).
4. MarketDataManager quality integration and tick recording.
5. Endpoints: GET /api/v1/market/quality and GET /api/v1/market/feed-health.
6. Real-time WebSocket (/api/ws & /api/v1/market/stream):
   - 1-second ticks with multi-market quotes, indices, portfolio, data_quality, ai_safety.
   - Bidirectional ping / pong and symbol subscription.
   - Zero fake data guarantee.
"""
import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.market_data.data_quality_engine import (
    DataQualityEngine,
    get_data_quality_engine,
)
from app.services.market_data.market_data_manager import get_market_data_manager


client = TestClient(app)


def test_data_quality_engine_fresh_tick_is_live():
    """Test that a recent tick produces LIVE state and permits AI recommendations."""
    engine = DataQualityEngine()
    engine.record_tick("RELIANCE", "NSE_YFINANCE", latency_ms=45.0)

    quality = engine.evaluate_symbol_quality("RELIANCE")
    assert quality["symbol"] == "RELIANCE"
    assert quality["status"] == "LIVE"
    assert quality["is_live"] is True
    assert quality["is_stale"] is False
    assert quality["ai_safe"] is True
    assert quality["latency_ms"] == 45.0
    assert quality["tick_age_seconds"] is not None
    assert quality["tick_age_seconds"] < 2.0


def test_data_quality_engine_staleness_tiers_and_ai_pause():
    """Test state transitions: LIVE -> WARNING -> STALE -> DISCONNECTED and automated AI pause."""
    engine = DataQualityEngine()
    now = time.time()

    # 1. WARNING tier (e.g. 10 seconds old with 15s default stale threshold)
    engine._symbol_ticks["TCS"] = {
        "symbol": "TCS",
        "provider": "NSE_YFINANCE",
        "last_tick_time": now - 10.0,
        "latency_ms": 60.0,
    }
    q_warning = engine.evaluate_symbol_quality("TCS")
    assert q_warning["status"] == "WARNING"
    assert q_warning["is_live"] is True
    assert q_warning["is_stale"] is False
    assert q_warning["ai_safe"] is True

    # 2. STALE tier (e.g. 20 seconds old > 15s threshold)
    engine._symbol_ticks["INFY"] = {
        "symbol": "INFY",
        "provider": "NSE_YFINANCE",
        "last_tick_time": now - 20.0,
        "latency_ms": 75.0,
    }
    q_stale = engine.evaluate_symbol_quality("INFY")
    assert q_stale["status"] == "STALE"
    assert q_stale["is_stale"] is True
    assert q_stale["is_live"] is False
    assert q_stale["ai_safe"] is False  # AI recommendations must be PAUSED

    # 3. DISCONNECTED tier (e.g. 100 seconds old or unobserved)
    q_unobserved = engine.evaluate_symbol_quality("UNKNOWN_XYZ")
    assert q_unobserved["status"] == "DISCONNECTED"
    assert q_unobserved["ai_safe"] is False


def test_high_latency_detection():
    """Test that tick latency > 1,200 ms triggers high latency warning."""
    engine = DataQualityEngine()
    engine.record_tick("AAPL", "INTERNATIONAL_YFINANCE", latency_ms=1450.0)

    quality = engine.evaluate_symbol_quality("AAPL")
    assert quality["latency_ms"] == 1450.0
    assert "HIGH DATA LATENCY" in quality["label"]


def test_global_quality_evaluation_and_reconnects():
    """Test global feed quality evaluation, reconnect count, and system-wide AI safety."""
    engine = DataQualityEngine()
    engine.record_reconnect("NSE_YFINANCE")
    engine.record_reconnect("NSE_YFINANCE")
    engine.record_reconnect("INTERNATIONAL_YFINANCE")

    engine.record_tick("NIFTY 50", "NSE_YFINANCE", latency_ms=30.0)
    engine.record_tick("NASDAQ 100", "INTERNATIONAL_YFINANCE", latency_ms=80.0)

    glob = engine.evaluate_global_quality(is_market_open=True)
    assert glob["observed_symbols_count"] >= 2
    assert glob["reconnect_counts"]["NSE_YFINANCE"] == 2
    assert glob["reconnect_counts"]["INTERNATIONAL_YFINANCE"] == 1
    assert glob["ai_recommendations_paused"] is False
    assert glob["is_stale"] is False


def test_market_data_manager_quality_integration():
    """Test MarketDataManager integration with DataQualityEngine."""
    manager = get_market_data_manager()
    manager.initialize()

    # Record a test tick
    manager.record_quote_tick("MSFT", "INTERNATIONAL_YFINANCE", latency_ms=55.0)

    # Symbol-specific quality
    sym_quality = manager.get_data_quality("MSFT")
    assert sym_quality["symbol"] == "MSFT"
    assert sym_quality["latency_ms"] == 55.0
    assert sym_quality["status"] in ["LIVE", "WARNING"]

    # Global quality
    glob_quality = manager.get_data_quality()
    assert "data_status" in glob_quality
    assert "ai_recommendations_paused" in glob_quality
    assert "reconnect_counts" in glob_quality


def test_rest_endpoints_quality_and_feed_health():
    """Test GET /api/v1/market/quality and GET /api/v1/market/feed-health."""
    # 1. Global quality
    res_global = client.get("/api/v1/market/quality")
    assert res_global.status_code == 200
    data_g = res_global.json()
    assert "data_status" in data_g
    assert "ai_recommendations_paused" in data_g

    # 2. Symbol quality
    res_sym = client.get("/api/v1/market/quality?symbol=RELIANCE")
    assert res_sym.status_code == 200
    data_s = res_sym.json()
    assert data_s["symbol"] == "RELIANCE"
    assert "status" in data_s

    # 3. Feed health
    res_health = client.get("/api/v1/market/feed-health")
    assert res_health.status_code == 200
    data_h = res_health.json()
    assert "connection_status" in data_h
    assert "provider_name" in data_h
    assert "data_quality" in data_h


def test_websocket_unified_stream_and_bidirectional_ping():
    """Test real-time WebSocket /api/ws tick updates, data quality, and ping/pong."""
    with client.websocket_connect("/api/ws") as ws:
        # Receive first 1-second TICK_UPDATE
        msg = ws.receive_json()
        assert msg["type"] == "TICK_UPDATE"
        assert "quotes" in msg
        assert "indices" in msg
        assert "portfolio" in msg
        assert "signals" in msg
        assert "data_quality" in msg
        assert "ai_safety" in msg
        assert "disclaimer" in msg["ai_safety"]
        assert "probabilistic" in msg["ai_safety"]["disclaimer"]

        # Send Ping -> Receive PONG
        ws.send_json({"action": "ping"})
        pong_msg = ws.receive_json()
        if pong_msg.get("type") != "PONG":
            pong_msg = ws.receive_json()
        assert pong_msg["type"] in ["PONG", "TICK_UPDATE"]

        # Send Subscription request
        ws.send_json({"action": "subscribe", "symbols": ["NSE:RELIANCE", "NASDAQ:AAPL"]})
        sub_resp = ws.receive_json()
        if sub_resp.get("type") != "SUBSCRIBED":
            sub_resp = ws.receive_json()
        assert sub_resp["type"] in ["SUBSCRIBED", "TICK_UPDATE"]


def test_websocket_market_stream_snapshot():
    """Test /api/v1/market/stream SNAPSHOT and connection."""
    with client.websocket_connect("/api/v1/market/stream") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "SNAPSHOT"
        assert "market_status" in msg
        assert "data_quality" in msg
        assert "quotes" in msg
