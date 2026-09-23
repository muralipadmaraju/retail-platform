import os

os.environ.setdefault("APP_VERSION", "4.2.1")
os.environ.setdefault("PAYMENT_MODE", "fixed")
os.environ.setdefault("FAIL_HEALTH", "false")

from app.app import app


def test_home():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert response.json["application"] == "retail-platform"


def test_payment_defect_fixed():
    client = app.test_client()
    response = client.get("/payment")
    assert response.status_code == 200
    assert response.json["defect_fixed"] is True


def test_health():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"
