"""Pruebas de la API base."""
from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "docs" in resp.json()
