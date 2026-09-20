import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_store
from app.models.db_models import TradeRecordModel

client = TestClient(app)


def test_audit_log_recording_and_retrieval():
    store = get_store()
    
    # 1. Log custom audit events
    store.log_audit('ORDER_EXECUTED', 'INFO', 'Filled BUY 10 RELIANCE @ 2950', {'qty': 10, 'symbol': 'RELIANCE'})
    store.log_audit('RISK_WARNING', 'WARNING', 'Max loss threshold approached', {'drawdown': 500.0})

    # 2. Retrieve audit trail via API
    resp = client.get('/api/records/audit')
    assert resp.status_code == 200
    logs = resp.json()
    assert len(logs) >= 2
    assert any(l['event_type'] == 'ORDER_EXECUTED' for l in logs)
    assert any(l['event_type'] == 'RISK_WARNING' for l in logs)


def test_trade_journal_records_and_summary():
    store = get_store()
    with store._lock:
        store.trades.append(
            TradeRecordModel(
                id='TRD-AUDIT-01',
                symbol='INFY',
                side='BUY',
                quantity=20,
                entry_price=1480.0,
                exit_price=1520.0,
                realized_pnl=800.0,
                pnl_percent=2.70,
                duration='Intraday',
                strategy='AI Momentum Ensemble',
                exit_reason='TAKE_PROFIT',
                status='CLOSED',
                opened_at='2026-09-12T09:15:00Z',
                closed_at='2026-09-12T10:45:00Z',
            )
        )

    # Test trades endpoint
    trades_resp = client.get('/api/records/trades')
    assert trades_resp.status_code == 200
    assert any(t['id'] == 'TRD-AUDIT-01' for t in trades_resp.json())

    # Test summary endpoint
    summary_resp = client.get('/api/records/summary')
    assert summary_resp.status_code == 200
    s_data = summary_resp.json()
    assert 'win_rate' in s_data
    assert 'audit_status' in s_data


def test_compliance_export_json_and_csv():
    # JSON Export
    json_resp = client.get('/api/records/export?format=json')
    assert json_resp.status_code == 200
    data = json_resp.json()
    assert 'compliance_standard' in data
    assert 'trades' in data
    assert 'audit_logs' in data

    # CSV Export
    csv_resp = client.get('/api/records/export?format=csv')
    assert csv_resp.status_code == 200
    assert 'text/csv' in csv_resp.headers.get('content-type', '')
    csv_text = csv_resp.text
    assert 'Trade_ID,Symbol,Side' in csv_text
