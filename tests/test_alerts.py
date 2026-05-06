from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import Claim, AlertConfig
from tests.conftest import TestingSessionLocal


@pytest.fixture()
def seed_alert_claims():
    db = TestingSessionLocal()
    now = datetime.now(timezone.utc)
    claims = [
        Claim(
            patient_id="PAT-001", cpt_code="99213",
            payer="BlueCross_Test", department="cardiology",
            expected_amount=500.0, status="denied",
            submitted_at=now - timedelta(days=5),
            denial_reason="Duplicate claim",
        ),
        Claim(
            patient_id="PAT-002", cpt_code="99214",
            payer="BlueCross_Test", department="cardiology",
            expected_amount=800.0, status="denied",
            submitted_at=now - timedelta(days=3),
            denial_reason="Prior auth required",
        ),
        Claim(
            patient_id="PAT-003", cpt_code="93000",
            payer="Aetna_Test", department="radiology",
            expected_amount=300.0, status="paid",
            submitted_at=now - timedelta(days=10),
            paid_at=now - timedelta(days=5),
            paid_amount=300.0,
        ),
    ]
    for c in claims:
        db.add(c)
    db.commit()
    db.close()


def test_alerts_requires_auth():
    client = TestClient(app)
    response = client.get("/alerts")
    assert response.status_code == 401


def test_configure_alert(client_with_token):
    response = client_with_token.post("/alerts/configure", json={
        "metric": "denial_rate",
        "threshold": 25.0,
        "operator": "gt",
        "webhook_url": "https://webhook.site/test",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["metric"] == "denial_rate"
    assert data["threshold"] == 25.0
    assert data["is_active"] == True
    assert "id" in data


def test_list_alerts(client_with_token):
    client_with_token.post("/alerts/configure", json={
        "metric": "denial_rate",
        "threshold": 25.0,
        "operator": "gt",
        "webhook_url": "https://webhook.site/test",
    })
    client_with_token.post("/alerts/configure", json={
        "metric": "ar_days",
        "threshold": 45.0,
        "operator": "gt",
        "webhook_url": "https://webhook.site/test",
    })
    response = client_with_token.get("/alerts")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_deactivate_alert(client_with_token):
    create_response = client_with_token.post("/alerts/configure", json={
        "metric": "denial_rate",
        "threshold": 25.0,
        "operator": "gt",
        "webhook_url": "https://webhook.site/test",
    })
    alert_id = create_response.json()["id"]

    response = client_with_token.delete(f"/alerts/{alert_id}")
    assert response.status_code == 204

    alerts = client_with_token.get("/alerts").json()
    assert not any(a["id"] == alert_id for a in alerts)


def test_deactivate_nonexistent_alert(client_with_token):
    response = client_with_token.delete("/alerts/99999")
    assert response.status_code == 404


def test_evaluate_alerts_no_triggers(client_with_token, seed_alert_claims):
    client_with_token.post("/alerts/configure", json={
        "metric": "denial_rate",
        "threshold": 90.0,
        "operator": "gt",
        "webhook_url": "https://webhook.site/test",
    })
    response = client_with_token.post("/alerts/evaluate")
    assert response.status_code == 200
    assert response.json() == []


def test_evaluate_alerts_triggers(client_with_token, seed_alert_claims):
    client_with_token.post("/alerts/configure", json={
        "metric": "denial_rate",
        "threshold": 10.0,
        "operator": "gt",
        "webhook_url": "https://webhook.site/test",
    })

    with patch(
        "app.services.alert_service.send_webhook",
        new_callable=AsyncMock,
        return_value=True,
    ):
        response = client_with_token.post("/alerts/evaluate")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["metric"] == "denial_rate"
    assert data[0]["webhook_sent"] == True
    assert data[0]["current_value"] > 10.0