import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine_test = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(bind=engine_test, autocommit=False, autoflush=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


client = TestClient(app)


def test_register_user():
    response = client.post("/auth/register", json={
        "name": "Luis Ochoa",
        "email": "luis@rcm.com",
        "role": "biller",
        "department": "cardiology",
        "password": "testpassword123",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "luis@rcm.com"
    assert "id" in data
    assert "hashed_password" not in data


def test_login_success():
    client.post("/auth/register", json={
        "name": "Luis Ochoa",
        "email": "luis@rcm.com",
        "role": "biller",
        "department": "cardiology",
        "password": "testpassword123",
    })
    response = client.post("/auth/token", data={
        "username": "luis@rcm.com",
        "password": "testpassword123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    client.post("/auth/register", json={
        "name": "Luis Ochoa",
        "email": "luis@rcm.com",
        "role": "biller",
        "department": "cardiology",
        "password": "testpassword123",
    })
    response = client.post("/auth/token", data={
        "username": "luis@rcm.com",
        "password": "wrong",
    })
    assert response.status_code == 401


def test_duplicate_email():
    payload = {
        "name": "Luis Ochoa",
        "email": "luis@rcm.com",
        "role": "biller",
        "department": "cardiology",
        "password": "testpassword123",
    }
    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400