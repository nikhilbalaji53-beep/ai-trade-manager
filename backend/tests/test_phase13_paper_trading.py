import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.market_data.market_data_manager import get_market_data_manager
from app.database import get_store

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_market_quotes(monkeypatch):
    mgr = get_market_data_manager()
    now_iso = '2026-09-12T10:00:00+05:30'
    mock_quote = {
        'symbol': 'INFY',
        'exchange': 'NSE',
        'name': 'Infosys Limited',
        'price': 1500.0,
        'last_price': 1500.0,
        'open': 1490.0,
        'high': 1515.0,
        'low': 1485.0,
        'previous_close': 1490.0,
        'change': 10.0,
        'change_percent': 0.67,
        'volume': 1500000,
        'avg_volume': 1400000,
        'market_cap': '₹6.2T',
        'pe_ratio': 26.5,
        'day_52w_high': 1900.0,
        'day_52w_low': 1300.0,
        'vwap': 1502.0,
        'rsi': 55.0,
        'trend': 'BULLISH',
        'sentiment_score': 0.45,
        'timestamp': now_iso,
        'data_status': 'LIVE_DELAYED',
        'data_source': 'NSE_LIVE_MOCK',
        'is_live': True,
        'stale': False,
    }
    mgr._cached_quotes['INFY'] = mock_quote
    monkeypatch.setattr(mgr, 'get_quote', lambda sym: mock_quote if sym.upper().replace('.NS', '') == 'INFY' else None)


def test_paper_account_reset_and_status():
    # 1. Reset account to 200,000 INR
    reset_resp = client.post(
        '/api/v1/paper/account/reset',
        json={
            'starting_capital': 200000.0,
            'currency': 'INR',
            'clear_existing_positions': True,
        },
    )
    assert reset_resp.status_code == 200
    data = reset_resp.json()
    assert data['starting_capital'] == 200000.0
    assert data['available_cash'] == 200000.0
    assert data['is_paper_trading'] is True
    assert data['currency'] == 'INR'

    # 2. Query account
    acc_resp = client.get('/api/v1/paper/account')
    assert acc_resp.status_code == 200
    acc_data = acc_resp.json()
    assert acc_data['available_cash'] == 200000.0


def test_paper_order_execution_and_positions():
    # Place a paper order for 10 INFY @ 1500 (15,000 notional)
    order_resp = client.post(
        '/api/v1/paper/orders',
        json={
            'symbol': 'INFY',
            'side': 'BUY',
            'order_type': 'MARKET',
            'quantity': 10,
            'stop_loss': 1450.0,
            'target': 1600.0,
            'notes': 'Phase 13 Paper Trade Test',
        },
    )
    assert order_resp.status_code == 200
    ord_data = order_resp.json()
    assert ord_data['status'] == 'FILLED'
    assert ord_data['symbol'] == 'INFY'
    assert ord_data['is_paper'] is True

    # Verify position is open
    pos_resp = client.get('/api/v1/paper/positions')
    assert pos_resp.status_code == 200
    positions = pos_resp.json()
    assert any(p['symbol'] == 'INFY' and p['quantity'] == 10 for p in positions)

    # Verify orders history
    orders_resp = client.get('/api/v1/paper/orders')
    assert orders_resp.status_code == 200
    orders = orders_resp.json()
    assert any(o['symbol'] == 'INFY' and o['status'] == 'FILLED' for o in orders)


def test_paper_order_risk_rejection():
    # Attempt order exceeding available cash
    rej_resp = client.post(
        '/api/v1/paper/orders',
        json={
            'symbol': 'INFY',
            'side': 'BUY',
            'order_type': 'MARKET',
            'quantity': 5000,  # 5000 * 1500 = 7.5M > 200k cash
            'stop_loss': 1450.0,
            'target': 1600.0,
        },
    )
    assert rej_resp.status_code == 400
    detail = rej_resp.json().get('detail', {})
    assert detail.get('error') == 'PAPER_ORDER_REJECTED'


def test_paper_pnl_summary():
    pnl_resp = client.get('/api/v1/paper/pnl')
    assert pnl_resp.status_code == 200
    data = pnl_resp.json()
    assert data['is_paper'] is True
    assert 'net_pnl' in data
    assert 'win_rate_pct' in data
    assert 'profit_factor' in data
