import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.indian_brokerage import calculate_indian_charges
from app.database import get_store
from app.models.db_models import TradeRecordModel

client = TestClient(app)


def test_indian_statutory_brokerage_intraday():
    # Buy 100 shares @ 1000, Sell @ 1050 (Intraday)
    # Buy value = 100,000, Sell value = 105,000, Turnover = 205,000
    res = calculate_indian_charges(
        side='BUY',
        quantity=100,
        entry_price=1000.0,
        exit_price=1050.0,
        trade_type='INTRADAY',
        exchange='NSE',
    )
    assert res['gross_pnl'] == 5000.0
    assert res['brokerage'] == 40.0  # min(20, 30) + min(20, 31.5) = 20 + 20 = 40.0
    assert res['stt'] == round(105000 * 0.00025, 2)  # 26.25
    assert res['stamp_duty'] == round(100000 * 0.00003, 2)  # 3.0
    assert res['total_charges'] > 0
    assert res['net_pnl'] == round(res['gross_pnl'] - res['total_charges'], 2)
    assert res['turnover'] == 205000.0


def test_indian_statutory_brokerage_delivery():
    # Delivery trade: zero brokerage, 0.1% STT on both sides, 0.015% stamp duty
    res = calculate_indian_charges(
        side='BUY',
        quantity=50,
        entry_price=2000.0,
        exit_price=2100.0,
        trade_type='DELIVERY',
        exchange='NSE',
    )
    assert res['brokerage'] == 0.0
    assert res['stt'] == round((100000 + 105000) * 0.001, 2)  # 205.0
    assert res['stamp_duty'] == round(100000 * 0.00015, 2)  # 15.0
    assert res['net_pnl'] < res['gross_pnl']


def test_portfolio_endpoints_and_metrics():
    # Test GET /api/portfolio
    p_resp = client.get('/api/portfolio')
    assert p_resp.status_code == 200
    p_data = p_resp.json()
    assert 'equity' in p_data
    assert 'cash' in p_data
    assert 'margin_available' in p_data

    # Test GET /api/v1/pnl
    pnl_resp = client.get('/api/v1/pnl')
    assert pnl_resp.status_code == 200
    pnl_data = pnl_resp.json()
    assert 'starting_capital' in pnl_data
    assert 'realized_pnl' in pnl_data


def test_performance_deck_zero_fake_data_and_computation():
    store = get_store()
    
    # 1. Performance deck with no trades
    with store._lock:
        store.trades.clear()

    perf_resp = client.get('/api/analytics/performance-deck')
    assert perf_resp.status_code == 200
    perf_data = perf_resp.json()
    assert perf_data['total_trades'] == 0
    assert perf_data['net_pnl'] == 0.0
    assert 'No closed trades found' in perf_data['data_note']

    # 2. Performance deck with real trades added
    with store._lock:
        store.trades.append(
            TradeRecordModel(
                id='TRD-TEST-1',
                symbol='TCS',
                side='BUY',
                quantity=10,
                entry_price=3500.0,
                exit_price=3600.0,
                realized_pnl=950.0,
                pnl_percent=2.85,
                duration='Intraday',
                strategy='Supertrend Trend Rider',
                exit_reason='TAKE_PROFIT',
                status='CLOSED',
                opened_at='2026-09-12T09:30:00Z',
                closed_at='2026-09-12T11:00:00Z',
            )
        )

    perf_resp_2 = client.get('/api/analytics/performance-deck')
    assert perf_resp_2.status_code == 200
    data_2 = perf_resp_2.json()
    assert data_2['total_trades'] == 1
    assert data_2['net_pnl'] == 950.0
    assert data_2['win_rate'] == 100.0
