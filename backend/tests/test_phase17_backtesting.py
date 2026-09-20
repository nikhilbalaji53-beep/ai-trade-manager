import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.backtesting_engine import run_strategy_backtest

client = TestClient(app)


def generate_mock_bars(count=100, start_price=2500.0):
    bars = []
    p = start_price
    for i in range(count):
        p = p * (1.0 + ((i % 5 - 2) * 0.005))
        bars.append({
            'timestamp': f'2026-09-12T{10 + (i // 60):02d}:{i % 60:02d}:00Z',
            'open': p - 2.0,
            'high': p + 8.0,
            'low': p - 6.0,
            'close': p,
            'volume': 50000 + i * 100,
        })
    return bars


def test_backtesting_strategies_execution(monkeypatch):
    mock_bars = generate_mock_bars(120, 2500.0)
    monkeypatch.setattr('app.services.backtesting_engine.generate_historical_candles', lambda sym, tf, cnt: mock_bars)

    strategies = [
        'AI Momentum Ensemble',
        'Supertrend Trend Rider',
        'Bollinger Mean Reversion',
        'Breakout Volatility',
    ]
    for strat in strategies:
        res = run_strategy_backtest(
            strategy_name=strat,
            symbol='RELIANCE',
            timeframe='1h',
            days_lookback=30,
            starting_capital=100000.0,
            risk_per_trade_pct=2.0,
            slippage_pct=0.05,
            commission_per_trade=20.0,
        )
        assert res['strategy_name'] == strat
        assert res['symbol'] == 'RELIANCE'
        assert 'total_return_pct' in res
        assert 'max_drawdown_pct' in res
        assert 'win_rate_pct' in res
        assert 'profit_factor' in res
        assert 'equity_curve' in res
        assert len(res['equity_curve']) > 0


def test_backtesting_insufficient_bars_zero_fake_data(monkeypatch):
    monkeypatch.setattr('app.services.backtesting_engine.generate_historical_candles', lambda sym, tf, cnt: [])
    with pytest.raises(ValueError) as exc:
        run_strategy_backtest(
            strategy_name='Supertrend Trend Rider',
            symbol='RELIANCE',
        )
    assert 'Insufficient historical candle data' in str(exc.value)


def test_backtesting_api_endpoint(monkeypatch):
    mock_bars = generate_mock_bars(120, 225.0)
    monkeypatch.setattr('app.services.backtesting_engine.generate_historical_candles', lambda sym, tf, cnt: mock_bars)

    resp = client.post(
        '/api/analytics/backtest',
        json={
            'strategy_name': 'Supertrend Trend Rider',
            'symbol': 'AAPL',
            'timeframe': '1h',
            'days_lookback': 30,
            'starting_capital': 50000.0,
            'risk_per_trade_pct': 2.0,
            'slippage_pct': 0.05,
            'commission_per_trade': 1.5,
            'stop_loss_pct': 2.5,
            'take_profit_pct': 5.0,
            'trailing_stop': True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['strategy_name'] == 'Supertrend Trend Rider'
    assert data['symbol'] == 'AAPL'
    assert 'sharpe_ratio' in data
    assert 'equity_curve' in data
