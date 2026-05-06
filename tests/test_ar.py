from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.models import Claim
from tests.conftest import TestingSessionLocal

import pytest


@pytest.fixture()
def seed_ar_claims():
    db = TestingSessionLocal()
    now = datetime.now(timezone.utc)
    claims = [
        Claim(
            patient_id="PAT-001", cpt_code="99213", payer="BlueCross_Test",
            department="cardiology", expected_amount=500.0, paid_amount=500.0,
            status="paid",
            submitted_at=now - timedelta(days=20),
            paid_at=now,
        ),
        Claim(
            patient_id="PAT-002", cpt_code="99214", payer="Aetna_Test",
            department="cardiology", expected_amount=800.0, paid_amount=800.0,
            status="paid",
            submitted_at=now - timedelta(days=60),
            paid_at=now - timedelta(days=20),
        ),
        Claim(
            patient_id="PAT-003", cpt_code="93000", payer="BlueCross_Test",
            department="radiology", expected_amount=300.0,
            status="pending",
            submitted_at=now - timedelta(days=15),
        ),
        Claim(
            patient_id="PAT-004", cpt_code="71046", payer="Cigna_Test",
            department="radiology", expected_amount=600.0,
            status="pending",
            submitted_at=now - timedelta(days=75),
        ),
        Claim(
            patient_id="PAT-005", cpt_code="80053", payer="Aetna_Test",
            department="laboratory", expected_amount=200.0,
            status="appealed",
            submitted_at=now - timedelta(days=45),
        ),
    ]
    for c in claims:
        db.add(c)
    db.commit()
    db.close()


def test_ar_days_requires_auth():
    client = TestClient(app)
    response = client.get("/ar/days")
    assert response.status_code == 401


def test_ar_days(client_with_token, seed_ar_claims):
    response = client_with_token.get("/ar/days")
    assert response.status_code == 200
    data = response.json()
    assert "average_ar_days" in data
    assert "benchmark_days" in data
    assert data["benchmark_days"] == 40.0
    assert "status" in data


def test_ar_days_above_benchmark(client_with_token, seed_ar_claims):
    response = client_with_token.get("/ar/days")
    data = response.json()
    assert data["average_ar_days"] > 0


def test_aging_buckets(client_with_token, seed_ar_claims):
    response = client_with_token.get("/ar/aging-buckets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for item in data:
        assert item["bucket"] in ["0-30", "31-60", "61-90", "90+"]


def test_aging_buckets_order(client_with_token, seed_ar_claims):
    response = client_with_token.get("/ar/aging-buckets")
    data = response.json()
    bucket_order = {"0-30": 0, "31-60": 1, "61-90": 2, "90+": 3}
    positions = [bucket_order[item["bucket"]] for item in data]
    assert positions == sorted(positions)


def test_aging_buckets_correct_classification(client_with_token, seed_ar_claims):
    response = client_with_token.get("/ar/aging-buckets")
    data = response.json()
    bucket_map = {item["bucket"]: item for item in data}
    assert "0-30" in bucket_map
    assert bucket_map["0-30"]["count"] == 1
    assert "61-90" in bucket_map
    assert bucket_map["61-90"]["count"] == 1


def test_ar_by_department(client_with_token, seed_ar_claims):
    response = client_with_token.get("/ar/by-department")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    departments = [item["department"] for item in data]
    assert "cardiology" in departments