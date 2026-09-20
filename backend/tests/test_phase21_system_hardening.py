import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.instrument_master import get_all_instruments, get_instrument_by_symbol
from app.services.market_data.market_data_manager import get_market_data_manager
from app.database import get_store

client = TestClient(app)


def test_multi_market_master_integrity():
    instruments = get_all_instruments()
    assert len(instruments) >= 50

    # Indian instrument verification
    reliance = get_instrument_by_symbol('RELIANCE')
    assert reliance is not None
    assert reliance['exchange'] == 'NSE'
    assert reliance['market'] == 'IN'
    assert reliance['currency'] == 'INR'
    assert reliance['currency_symbol'] == '₹'

    # US instrument verification
    nvda = get_instrument_by_symbol('NVDA')
    assert nvda is not None
    assert nvda['exchange'] == 'NASDAQ'
    assert nvda['market'] == 'US'
    assert nvda['currency'] == 'USD'
    assert nvda['currency_symbol'] == '$'


def test_zero_fake_data_policy_across_endpoints():
    # Non-existent symbol must return 404 with QUOTE_NOT_AVAILABLE, not fake numbers
    resp = client.get('/api/v1/market/quote/NONEXISTENT_TICKER_99999')
    assert resp.status_code == 404
    err = resp.json().get('detail', {})
    assert err.get('error') == 'QUOTE_NOT_AVAILABLE'


def test_probabilistic_safety_and_disclaimers():
    # 1. Trade Manager evaluate endpoint
    resp = client.post(
        '/api/v1/trade-manager/evaluate',
        json={
            'symbol': 'AAPL',
            'side': 'BUY',
            'entry_price': 220.0,
            'current_price': 225.0,
            'stop_loss': 214.5,
            'take_profit': 235.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert 'disclaimer' in data
    assert 'probabilistic' in data['disclaimer'].lower()


def test_complete_end_to_end_trading_and_audit_cycle():
    # Reset account
    reset_resp = client.post(
        '/api/v1/paper/account/reset',
        json={'starting_capital': 500000.0, 'currency': 'INR', 'clear_existing_positions': True},
    )
    assert reset_resp.status_code == 200

    # System status check
    sys_resp = client.get('/api/system/status')
    assert sys_resp.status_code == 200
    assert sys_resp.json()['status'] == 'operational'

    # Audit log check
    audit_resp = client.get('/api/records/audit')
    assert audit_resp.status_code == 200
    assert len(audit_resp.json()) > 0
