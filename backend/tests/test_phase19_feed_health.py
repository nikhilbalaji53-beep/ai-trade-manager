import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.market_data.feed_health import FeedHealthMonitor

client = TestClient(app)


def test_feed_health_monitor_ticks_and_rejections():
    fhm = FeedHealthMonitor()
    fhm.set_provider('NSE_YFINANCE')
    assert fhm._provider_name == 'NSE_YFINANCE'

    # Record ticks
    fhm.record_tick('RELIANCE', latency_ms=45.2)
    fhm.record_tick('TCS', latency_ms=38.1)
    assert fhm._last_tick_symbol == 'TCS'
    assert fhm._last_latency_ms == 38.1
    assert fhm.get_ticks_per_minute() >= 2.0

    # Record rejected ticks
    fhm.record_rejected_tick('BAD_SYM', 'Invalid zero price')
    assert fhm._rejected_ticks == 1
    assert len(fhm._error_log) == 1

    # Record stale tick
    fhm.record_stale_tick('INFY')
    assert fhm._stale_ticks == 1


def test_feed_health_connection_status_states():
    fhm = FeedHealthMonitor()

    # When disconnected
    assert fhm.get_connection_status(is_provider_connected=False) == 'DISCONNECTED'

    # When connected but no tick yet
    assert fhm.get_connection_status(is_provider_connected=True) == 'AWAITING_FIRST_TICK'

    # When tick is recent (<60s)
    fhm.record_tick('RELIANCE')
    assert fhm.get_connection_status(is_provider_connected=True) == 'LIVE_DELAYED'

    # Simulated stale (tick 120s ago)
    fhm._last_tick_time = time.time() - 120
    assert fhm.get_connection_status(is_provider_connected=True) == 'STALE'


def test_health_endpoints():
    h_resp = client.get('/health')
    assert h_resp.status_code == 200
    h_data = h_resp.json()
    assert 'feed_health' in h_data
    assert 'market_data' in h_data

    fh_resp = client.get('/api/v1/market/feed-health')
    assert fh_resp.status_code == 200
    fh_data = fh_resp.json()
    assert 'connection_status' in fh_data
    assert 'data_quality' in fh_data
