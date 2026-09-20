import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.risk_engine import validate_order, assess_portfolio
from app.database import RiskSettings, get_store
from app.models.db_models import PositionModel

client = TestClient(app)


def test_validate_order_cash_and_position_limits():
    settings = RiskSettings()
    settings.max_single_position_pct = 25.0
    settings.max_portfolio_risk_pct = 75.0
    settings.require_stop_loss = True

    cash = 100000.0
    equity = 100000.0
    positions = []

    # 1. Reject when notional > cash
    passed, msg = validate_order(
        cash=5000.0,
        equity=equity,
        positions=positions,
        symbol='RELIANCE',
        side='BUY',
        notional=10000.0,
        stop_loss=2400.0,
        risk_settings=settings,
    )
    assert not passed
    assert 'Insufficient available cash' in msg

    # 2. Reject when single position exceeds 25% of equity (25,000)
    passed, msg = validate_order(
        cash=cash,
        equity=equity,
        positions=positions,
        symbol='RELIANCE',
        side='BUY',
        notional=30000.0,
        stop_loss=2400.0,
        risk_settings=settings,
    )
    assert not passed
    assert 'exposure limit' in msg.lower()

    # 3. Reject when stop loss is missing
    passed, msg = validate_order(
        cash=cash,
        equity=equity,
        positions=positions,
        symbol='RELIANCE',
        side='BUY',
        notional=20000.0,
        stop_loss=None,
        risk_settings=settings,
    )
    assert not passed
    assert 'Stop loss is required' in msg

    # 4. Pass when all rules met
    passed, msg = validate_order(
        cash=cash,
        equity=equity,
        positions=positions,
        symbol='RELIANCE',
        side='BUY',
        notional=20000.0,
        stop_loss=2400.0,
        risk_settings=settings,
    )
    assert passed
    assert 'PASSED' in msg


def test_assess_portfolio_var_and_guardrails():
    positions = [
        {'symbol': 'RELIANCE', 'side': 'BUY', 'market_value': 25000.0, 'unrealized_pnl': 500.0, 'risk_level': 'Low'},
        {'symbol': 'TCS', 'side': 'BUY', 'market_value': 25000.0, 'unrealized_pnl': -200.0, 'risk_level': 'Low'},
    ]
    cash = 50000.0
    capital = 100000.0

    res = assess_portfolio(cash=cash, starting_capital=capital, positions=positions)
    assert 'score' in res
    assert 'var_95_pct' in res
    assert 'guardrails' in res
    assert len(res['guardrails']) >= 4


def test_risk_settings_api_update():
    resp = client.post(
        '/api/portfolio/risk/settings',
        json={
            'max_portfolio_risk_pct': 70.0,
            'max_single_position_pct': 25.0,
            'max_daily_loss': 12000.0,
        },
    )
    assert resp.status_code == 200
    assert resp.json()['status'] == 'success'


def test_emergency_kill_switch_api():
    resp = client.post('/api/v1/risk/kill-switch')
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'EXECUTED'
    assert 'results' in data
