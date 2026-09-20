import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_store

client = TestClient(app)


def test_alerts_crud_lifecycle():
    store = get_store()

    # 1. Clear existing alerts
    clear_resp = client.post('/api/alerts/clear')
    assert clear_resp.status_code == 200

    # 2. Create a custom alert
    create_resp = client.post(
        '/api/alerts',
        json={
            'symbol': 'TCS',
            'alert_type': 'PRICE_ABOVE',
            'target_value': 4200.0,
            'notes': 'Resistance breakout trigger',
            'severity': 'yellow',
        },
    )
    assert create_resp.status_code == 201
    alert_obj = create_resp.json()['alert']
    alert_id = alert_obj['id']

    # 3. List alerts
    list_resp = client.get('/api/alerts')
    assert list_resp.status_code == 200
    alerts = list_resp.json()
    assert any(a['id'] == alert_id for a in alerts)

    # 4. Mark read
    read_resp = client.post(f'/api/alerts/{alert_id}/read')
    assert read_resp.status_code == 200

    # Verify marked read
    list_resp_2 = client.get('/api/alerts')
    target = next((a for a in list_resp_2.json() if a['id'] == alert_id), None)
    assert target is not None
    assert target['read'] is True

    # 5. Clear all
    client.post('/api/alerts/clear')
    assert len(client.get('/api/alerts').json()) == 0
