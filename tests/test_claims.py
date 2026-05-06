from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import Claim, Staff
from tests.conftest import TestingSessionLocal

import pytest


@pytest.fixture()
def seed_claims():
    db = TestingSessionLocal()
    now = datetime.now(timezone.utc)
    claims = [
        Claim(
            patient_id="PAT-001",
            cpt_code="99213",
            payer="BlueCross_Test",
            department="cardiology",
            expected_amount=500.0,
            status="denied",
            submitted_at=now - timedelta(days=10),
            denial_reason="Duplicate claim",
        ),
        Claim(
            patient_id="PAT-002",
            cpt_code="99214",
            payer="BlueCross_Test",
            department="cardiology",
            expected_amount=800.0,
            paid_amount=800.0,
            status="paid",
            submitted_at=now - timedelta(days=8),
            paid_at=now - timedelta(days=3),
        ),
        Claim(
            patient_id="PAT-003",
            cpt_code="93000",
            payer="Aetna_Test",
            department="radiology",
            expected_amount=300.0,
            status="denied",
            submitted_at=now - timedelta(days=5),
            denial_reason="Prior auth required",
        ),
    ]
    for c in claims:
        db.add(c)
    db.commit()
    db.close()


def test_list_claims_requires_auth():
    client = TestClient(app)
    response = client.get("/claims")
    assert response.status_code == 401


def test_list_claims(client_with_token, seed_claims):
    response = client_with_token.get("/claims")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_list_claims_filter_by_payer(client_with_token, seed_claims):
    response = client_with_token.get("/claims?payer=Aetna_Test")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["payer"] == "Aetna_Test"


def test_get_claim_by_id(client_with_token, seed_claims):
    all_claims = client_with_token.get("/claims").json()
    claim_id = all_claims[0]["id"]
    response = client_with_token.get(f"/claims/{claim_id}")
    assert response.status_code == 200
    assert response.json()["id"] == claim_id


def test_get_claim_not_found(client_with_token):
    response = client_with_token.get("/claims/99999")
    assert response.status_code == 404


def test_denial_rate(client_with_token, seed_claims):
    response = client_with_token.get("/claims/denial-rate")
    assert response.status_code == 200
    data = response.json()
    bluecross = next(r for r in data if r["payer"] == "BlueCross_Test")
    assert bluecross["total"] == 2
    assert bluecross["denied"] == 1
    assert bluecross["rate"] == 50.0


def test_denial_rate_filter_by_payer(client_with_token, seed_claims):
    response = client_with_token.get("/claims/denial-rate?payer=Aetna_Test")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["rate"] == 100.0


def test_create_claim(client_with_token):
    payload = {
        "patient_id": "PAT-NEW",
        "cpt_code": "99215",
        "payer": "Cigna_Test",
        "expected_amount": 1200.0,
        "status": "pending",
        "submitted_at": "2024-06-01T10:00:00Z",
    }
    response = client_with_token.post("/claims", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == "PAT-NEW"
    assert "id" in data