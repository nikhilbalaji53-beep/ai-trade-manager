import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.broker_connector import IndianBrokerConnector, get_broker_connector

client = TestClient(app)


def test_supported_brokers_and_instances():
    expected = [
        'ZERODHA_KITE',
        'UPSTOX_API',
        'ANGEL_ONE',
        'FYERS_API',
        'SHOONYA_FINVASIA',
        'DHAN_HQ',
        'PAPER_BROKER',
    ]
    for b_name in expected:
        conn = get_broker_connector(b_name)
        assert conn.broker_name == b_name
        assert isinstance(conn, IndianBrokerConnector)


def test_broker_order_lifecycle():
    conn = get_broker_connector('ZERODHA_KITE')

    # 1. Place order
    res_place = conn.place_order(
        symbol='RELIANCE',
        side='BUY',
        quantity=25,
        order_type='LIMIT',
        price=2900.0,
        trigger_price=2850.0,
        exchange='NSE',
        product='MIS',
    )
    assert res_place['status'] == 'FILLED'
    assert res_place['symbol'] == 'RELIANCE'
    assert res_place['order_id'].startswith('NSE-')
    assert res_place['exchange_order_id'].startswith('EXCH-')

    # 2. Modify order
    res_mod = conn.modify_order(
        order_id=res_place['order_id'],
        quantity=30,
        price=2910.0,
    )
    assert res_mod['status'] == 'MODIFIED'
    assert res_mod['quantity'] == 30

    # 3. Cancel order
    res_cancel = conn.cancel_order(order_id=res_place['order_id'])
    assert res_cancel['status'] == 'CANCELLED'


def test_system_brokers_api_endpoint():
    resp = client.get('/api/system/brokers')
    assert resp.status_code == 200
    data = resp.json()
    assert data['count'] >= 7
    broker_names = [b['broker'] for b in data['brokers']]
    assert 'ZERODHA_KITE' in broker_names
    assert 'PAPER_BROKER' in broker_names
    assert 'UPSTOX_API' in broker_names
