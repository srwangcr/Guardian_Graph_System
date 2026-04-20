import importlib
import os

from fastapi.testclient import TestClient


def test_api_token_flow_and_protected_endpoints(monkeypatch):
    monkeypatch.setenv("GGS_CONFIG_PATH", "tests/test_config.yaml")

    # Ensure module reads patched config path.
    import utils.api_server as api_server

    importlib.reload(api_server)

    client = TestClient(api_server.app)

    token_response = client.post(
        "/token",
        data={"username": "test", "password": "test"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]

    health_response = client.get("/v1/health", headers={"Authorization": f"Bearer {token}"})
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"



def test_api_rejects_missing_token(monkeypatch):
    monkeypatch.setenv("GGS_CONFIG_PATH", "tests/test_config.yaml")

    import utils.api_server as api_server

    importlib.reload(api_server)

    client = TestClient(api_server.app)
    response = client.get("/v1/health")
    assert response.status_code in (401, 403)
