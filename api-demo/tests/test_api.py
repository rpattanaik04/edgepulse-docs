"""Smoke tests that prove the documented behavior of the demo API."""

import pytest
from fastapi.testclient import TestClient

from app import store
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_data():
    store.seed()


@pytest.fixture()
def auth():
    r = client.post(
        "/api/v1/auth/token",
        json={"client_id": "demo-client", "client_secret": "demo-secret"},
    )
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_health_needs_no_auth():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_timestamps_use_utc_z_format():
    """Every endpoint must return UTC timestamps in the same ...Z format."""
    assert client.get("/api/v1/health").json()["time"].endswith("Z")


def test_dashboard_is_served():
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "EdgePulse" in r.text and r.headers["content-type"].startswith("text/html")
    root = client.get("/", follow_redirects=False)
    assert root.status_code in (302, 307) and root.headers["location"] == "/dashboard"


def test_openapi_matches_real_error_format():
    """The published spec must describe the error format the API really returns."""
    spec = client.get("/openapi.json").json()
    assert "HTTPValidationError" not in spec["components"]["schemas"]
    r = client.post("/api/v1/auth/token", json={})
    assert r.status_code == 422
    body = r.json()["error"]
    assert body["code"] == "validation_error"
    assert {d["field"] for d in body["details"]} == {"client_id", "client_secret"}


def test_token_success_shape():
    r = client.post(
        "/api/v1/auth/token",
        json={"client_id": "demo-client", "client_secret": "demo-secret"},
    )
    body = r.json()
    assert body["token_type"] == "Bearer"
    assert body["expires_in"] == 3600


def test_token_bad_credentials():
    r = client.post("/api/v1/auth/token", json={"client_id": "x", "client_secret": "y"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "invalid_credentials"


def test_missing_token_rejected():
    r = client.get("/api/v1/devices")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


def test_list_devices_and_filter(auth):
    r = client.get("/api/v1/devices", headers=auth)
    assert r.json()["total"] == 5
    r = client.get("/api/v1/devices?status=online&site=Pune Plant", headers=auth)
    assert {d["id"] for d in r.json()["items"]} == {"dev_1001", "dev_1002"}


def test_pagination(auth):
    r = client.get("/api/v1/devices?limit=2&offset=4", headers=auth)
    body = r.json()
    assert len(body["items"]) == 1 and body["total"] == 5


def test_create_get_update_delete_device(auth):
    r = client.post(
        "/api/v1/devices",
        headers=auth,
        json={"name": "Test Gateway 06", "site": "Pune Plant", "protocol": "mqtt"},
    )
    assert r.status_code == 201
    dev_id = r.json()["id"]
    assert r.json()["status"] == "offline"
    assert client.get(f"/api/v1/devices/{dev_id}", headers=auth).status_code == 200
    r = client.patch(f"/api/v1/devices/{dev_id}", headers=auth, json={"status": "maintenance"})
    assert r.json()["status"] == "maintenance"
    assert client.delete(f"/api/v1/devices/{dev_id}", headers=auth).status_code == 204
    assert client.get(f"/api/v1/devices/{dev_id}", headers=auth).status_code == 404


def test_validation_error_shape(auth):
    r = client.post("/api/v1/devices", headers=auth, json={"name": "x", "site": "P"})
    assert r.status_code == 422
    body = r.json()["error"]
    assert body["code"] == "validation_error"
    assert {d["field"] for d in body["details"]} == {"name", "site"}


def test_device_not_found(auth):
    r = client.get("/api/v1/devices/dev_9999", headers=auth)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "device_not_found"


def test_telemetry_list_newest_first(auth):
    r = client.get("/api/v1/devices/dev_1001/telemetry?limit=3", headers=auth)
    items = r.json()["items"]
    assert len(items) == 3
    assert items[0]["timestamp"] >= items[1]["timestamp"] >= items[2]["timestamp"]


def test_telemetry_submit_marks_device_online(auth):
    r = client.post(
        "/api/v1/devices/dev_1005/telemetry",
        headers=auth,
        json={"temperature_c": 70.0, "vibration_mm_s": 2.0, "pressure_kpa": 400.0},
    )
    assert r.status_code == 201
    assert client.get("/api/v1/devices/dev_1005", headers=auth).json()["status"] == "online"


def test_high_vibration_raises_critical_alert(auth):
    before = client.get("/api/v1/alerts?severity=critical", headers=auth).json()["total"]
    client.post(
        "/api/v1/devices/dev_1001/telemetry",
        headers=auth,
        json={"temperature_c": 70.0, "vibration_mm_s": 6.2, "pressure_kpa": 400.0},
    )
    after = client.get("/api/v1/alerts?severity=critical", headers=auth).json()["total"]
    assert after == before + 1


def test_acknowledge_alert_flow(auth):
    r = client.post("/api/v1/alerts/alt_5001/acknowledge", headers=auth)
    assert r.status_code == 200
    assert r.json()["state"] == "acknowledged"
    r = client.post("/api/v1/alerts/alt_5001/acknowledge", headers=auth)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "alert_already_acknowledged"


def test_alert_not_found(auth):
    r = client.post("/api/v1/alerts/alt_0000/acknowledge", headers=auth)
    assert r.status_code == 404
