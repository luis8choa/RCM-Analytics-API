from datetime import datetime, timezone, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import Claim, Staff, StaffActivity
from app.auth import hash_password
from tests.conftest import TestingSessionLocal


@pytest.fixture()
def seed_staff_data():
    db = TestingSessionLocal()
    now = datetime.now(timezone.utc)

    staff_members = [
        Staff(
            name="Ana Billing",
            email="ana@rcm.com",
            role="biller",
            department="cardiology",
            hashed_password=hash_password("pass123"),
            is_active=True,
        ),
        Staff(
            name="Bob Coder",
            email="bob@rcm.com",
            role="coder",
            department="radiology",
            hashed_password=hash_password("pass123"),
            is_active=True,
        ),
        Staff(
            name="Carol Collector",
            email="carol@rcm.com",
            role="collector",
            department="laboratory",
            hashed_password=hash_password("pass123"),
            is_active=True,
        ),
    ]
    for s in staff_members:
        db.add(s)
    db.commit()
    for s in staff_members:
        db.refresh(s)

    claims = [
        Claim(
            patient_id="PAT-001", cpt_code="99213",
            payer="BlueCross_Test", department="cardiology",
            expected_amount=500.0, status="paid",
            submitted_at=now - timedelta(days=10),
            paid_at=now - timedelta(days=5),
            paid_amount=500.0,
        ),
        Claim(
            patient_id="PAT-002", cpt_code="99214",
            payer="Aetna_Test", department="radiology",
            expected_amount=800.0, status="denied",
            submitted_at=now - timedelta(days=8),
            denial_reason="Prior auth required",
        ),
        Claim(
            patient_id="PAT-003", cpt_code="93000",
            payer="BlueCross_Test", department="cardiology",
            expected_amount=300.0, status="pending",
            submitted_at=now - timedelta(days=3),
        ),
    ]
    for c in claims:
        db.add(c)
    db.commit()
    for c in claims:
        db.refresh(c)

    activities = [
        StaffActivity(
            staff_id=staff_members[0].id,
            claim_id=claims[0].id,
            action="submitted",
            error_flag=False,
            timestamp=now - timedelta(days=10),
        ),
        StaffActivity(
            staff_id=staff_members[0].id,
            claim_id=claims[1].id,
            action="reviewed",
            error_flag=True,
            timestamp=now - timedelta(days=8),
        ),
        StaffActivity(
            staff_id=staff_members[1].id,
            claim_id=claims[1].id,
            action="corrected",
            error_flag=False,
            timestamp=now - timedelta(days=7),
        ),
        StaffActivity(
            staff_id=staff_members[1].id,
            claim_id=claims[2].id,
            action="submitted",
            error_flag=False,
            timestamp=now - timedelta(days=3),
        ),
        StaffActivity(
            staff_id=staff_members[2].id,
            claim_id=claims[0].id,
            action="closed",
            error_flag=True,
            timestamp=now - timedelta(days=5),
        ),
    ]
    for a in activities:
        db.add(a)
    db.commit()
    db.close()


def test_productivity_requires_auth():
    client = TestClient(app)
    response = client.get("/staff/productivity")
    assert response.status_code == 401


def test_productivity(client_with_token, seed_staff_data):
    response = client_with_token.get("/staff/productivity")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    first = data[0]
    assert "staff_id" in first
    assert "name" in first
    assert "claims_processed" in first
    assert "team_average" in first
    assert "performance" in first
    assert first["performance"] in ["above_average", "average", "below_average"]


def test_productivity_amounts(client_with_token, seed_staff_data):
    response = client_with_token.get("/staff/productivity")
    data = response.json()
    for item in data:
        assert item["total_amount"] >= 0
        assert item["claims_processed"] > 0
        assert item["daily_average"] >= 0


def test_error_rate_requires_auth():
    client = TestClient(app)
    response = client.get("/staff/error-rate")
    assert response.status_code == 401


def test_error_rate(client_with_token, seed_staff_data):
    response = client_with_token.get("/staff/error-rate")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for item in data:
        assert "error_rate" in item
        assert 0.0 <= item["error_rate"] <= 100.0


def test_error_rate_ordered_by_errors(client_with_token, seed_staff_data):
    response = client_with_token.get("/staff/error-rate")
    data = response.json()
    errors = [item["errors"] for item in data]
    assert errors == sorted(errors, reverse=True)


def test_error_rate_ana_has_one_error(client_with_token, seed_staff_data):
    response = client_with_token.get("/staff/error-rate")
    data = response.json()
    ana = next((r for r in data if r["name"] == "Ana Billing"), None)
    assert ana is not None
    assert ana["total_actions"] == 2
    assert ana["errors"] == 1
    assert ana["error_rate"] == 50.0


def test_workload_requires_auth():
    client = TestClient(app)
    response = client.get("/staff/workload")
    assert response.status_code == 401


def test_workload(client_with_token, seed_staff_data):
    response = client_with_token.get("/staff/workload")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for item in data:
        assert "staff_id" in item
        assert "name" in item
        assert "pending_claims" in item


def test_workload_ordered_by_pending(client_with_token, seed_staff_data):
    response = client_with_token.get("/staff/workload")
    data = response.json()
    counts = [item["pending_claims"] for item in data]
    assert counts == sorted(counts, reverse=True)