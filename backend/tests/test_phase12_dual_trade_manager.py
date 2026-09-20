import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.trailing_stop import (
    evaluate_profit_manager,
    evaluate_loss_manager,
    evaluate_ai_trade_manager,
    evaluate_profit_protection_step,
)
from app.services.trade_manager import TradeManager
from app.database import PortfolioStore
from app.models.db_models import PositionModel
from app.services.market_data.market_data_manager import get_market_data_manager

client = TestClient(app)


def test_profit_manager_step_ladder_ratcheting():
    entry = 1000.0
    initial_stop = 975.0

    res_1 = evaluate_profit_manager('BUY', entry, 1010.0, initial_stop, 1010.0, 1100.0)
    assert res_1['new_stop'] == initial_stop
    assert res_1['action'] == 'HOLD'

    res_be = evaluate_profit_manager('BUY', entry, 1018.0, initial_stop, 1018.0, 1100.0)
    assert res_be['new_stop'] == 1000.0
    assert res_be['action'] == 'TRAIL_STOP'

    res_4 = evaluate_profit_manager('BUY', entry, 1045.0, 1000.0, 1045.0, 1100.0)
    assert res_4['new_stop'] == 1020.0
    assert res_4['action'] == 'TRAIL_STOP'

    res_6 = evaluate_profit_manager('BUY', entry, 1065.0, 1020.0, 1065.0, 1100.0)
    assert res_6['new_stop'] == 1035.0

    res_9 = evaluate_profit_manager('BUY', entry, 1090.0, 1035.0, 1090.0, 1100.0)
    assert res_9['new_stop'] == 1055.0


def test_profit_manager_target_exit_and_partial():
    entry = 1000.0
    tp1 = 1060.0
    tp2 = 1100.0

    res_tp = evaluate_profit_manager('BUY', entry, 1100.0, 1055.0, 1100.0, 1100.0)
    assert res_tp['action'] == 'TARGET_EXIT'

    res_partial = evaluate_profit_manager('BUY', entry, 1060.0, 1020.0, 1060.0, 1100.0, take_profit_2=tp2)
    assert res_partial['action'] in ['PARTIAL_EXIT', 'TRAIL_STOP']


def test_loss_manager_recover_watch_and_sl_cut():
    entry = 1000.0
    sl = 970.0

    res_pullback = evaluate_loss_manager('BUY', entry, 992.0, sl, max_loss=5000.0, quantity=10.0)
    assert res_pullback['action'] == 'RECOVER_WATCH'
    assert res_pullback['is_sl_hit'] is False

    res_hold = evaluate_loss_manager('BUY', entry, 980.0, sl, max_loss=5000.0, quantity=10.0)
    assert res_hold['action'] == 'HOLD'
    assert res_hold['is_sl_hit'] is False

    res_exit = evaluate_loss_manager('BUY', entry, 968.0, sl, max_loss=5000.0, quantity=10.0)
    assert res_exit['action'] == 'EXIT'
    assert res_exit['is_sl_hit'] is True

    res_max_loss = evaluate_loss_manager('BUY', entry, 975.0, 950.0, max_loss=200.0, quantity=10.0)
    assert res_max_loss['action'] == 'EXIT'


def test_evaluate_ai_trade_manager_branch_selection():
    res_profit = evaluate_ai_trade_manager(
        side='BUY',
        entry_price=100.0,
        current_price=105.0,
        stop_loss=95.0,
        trailing_stop=95.0,
        take_profit=115.0,
        highest_price=105.0,
        lowest_price=99.0,
    )
    assert res_profit['branch'] == 'PROFIT_MANAGER'
    assert res_profit['pnl_state'] == 'PROFIT'

    res_loss = evaluate_ai_trade_manager(
        side='BUY',
        entry_price=100.0,
        current_price=98.0,
        stop_loss=95.0,
        trailing_stop=95.0,
        take_profit=115.0,
        highest_price=100.0,
        lowest_price=98.0,
    )
    assert res_loss['branch'] == 'LOSS_MANAGER'
    assert res_loss['pnl_state'] == 'LOSS'


def test_evaluate_live_positions_with_zero_fake_data():
    store = PortfolioStore(100000.0)
    tm = TradeManager(store)

    pos = PositionModel(
        symbol='NONEXISTENT_STALE_SYM',
        side='BUY',
        quantity=10,
        entry_price=500.0,
        current_price=500.0,
        market_value=5000.0,
        unrealized_pnl=0.0,
        pnl_percent=0.0,
        stop_loss=480.0,
        trailing_stop=480.0,
        take_profit=550.0,
        risk_level='Low',
        highest_price=500.0,
        lowest_price=500.0,
        break_even_activated=False,
    )
    store.positions['NONEXISTENT_STALE_SYM'] = pos

    tm.evaluate_live_positions()

    assert 'NONEXISTENT_STALE_SYM' in store.positions
    assert store.positions['NONEXISTENT_STALE_SYM'].data_status == 'DATA_STALE'


def test_api_trade_manager_evaluate_endpoint():
    resp = client.post(
        '/api/v1/trade-manager/evaluate',
        json={
            'symbol': 'RELIANCE',
            'side': 'BUY',
            'entry_price': 2500.0,
            'current_price': 2650.0,
            'stop_loss': 2437.5,
            'take_profit': 2750.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['branch'] == 'PROFIT_MANAGER'
    assert data['new_stop'] > 2437.5
    assert 'probabilistic' in data['disclaimer'].lower()
