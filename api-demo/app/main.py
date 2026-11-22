"""EdgePulse demo API.

A small, working REST API used to support the EdgePulse documentation set.
Data is fictional and held in memory; it resets whenever the server restarts.
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import store
from .models import (
    Alert,
    AlertList,
    AlertState,
    Device,
    DeviceCreate,
    DeviceList,
    DeviceStatus,
    DeviceUpdate,
    ErrorResponse,
    HealthResponse,
    Severity,
    TelemetryCreate,
    TelemetryList,
    TelemetryReading,
    TokenRequest,
    TokenResponse,
)

API_VERSION = "1.2.0"
TOKEN_TTL_SECONDS = 3600
VIBRATION_ALERT_LIMIT_MM_S = 5.0

# Public demo credentials. Override with environment variables when hosting.
CLIENT_ID = os.getenv("EDGEPULSE_CLIENT_ID", "demo-client")
CLIENT_SECRET = os.getenv("EDGEPULSE_CLIENT_SECRET", "demo-secret")

TAGS = [
    {"name": "Health", "description": "Service availability. No authentication required."},
    {"name": "Authentication", "description": "Exchange client credentials for a bearer token."},
    {"name": "Devices", "description": "Register and manage edge devices."},
    {"name": "Telemetry", "description": "Send and read sensor readings."},
    {"name": "Alerts", "description": "List and acknowledge alerts."},
]

app = FastAPI(
    title="EdgePulse API",
    version=API_VERSION,
    summary="REST API for monitoring industrial edge devices.",
    description=(
        "EdgePulse is a **fictional** IIoT monitoring platform created for a documentation "
        "portfolio. This API is real and runnable, but all data is fictional and resets "
        "on restart.\n\n"
        "Authenticate with `POST /api/v1/auth/token`, then send the token as "
        "`Authorization: Bearer <token>`."
    ),
    openapi_tags=TAGS,
    contact={"name": "Rakesh Pattanaik", "url": "https://github.com/rpattanaik04"},
    license_info={"name": "MIT", "identifier": "MIT"},
)

bearer_scheme = HTTPBearer(auto_error=False, description="Token from POST /api/v1/auth/token")
_tokens: dict[str, datetime] = {}


# ---------- Error handling: one consistent JSON error shape ----------

def _error(status_code: int, code: str, message: str, details: Optional[list] = None):
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_: Request, exc: StarletteHTTPException):
    messages = {
        "unauthorized": "Missing, invalid or expired access token.",
        "invalid_credentials": "The client ID or client secret is incorrect.",
        "device_not_found": "No device exists with the given ID.",
        "alert_not_found": "No alert exists with the given ID.",
        "alert_already_acknowledged": "This alert has already been acknowledged.",
    }
    if exc.detail in messages:
        return _error(exc.status_code, exc.detail, messages[exc.detail])
    return _error(exc.status_code, "http_error", str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    details = [
        {"field": ".".join(str(p) for p in e["loc"] if p != "body"), "issue": e["msg"]}
        for e in exc.errors()
    ]
    return _error(422, "validation_error", "The request contains invalid data.", details)


# ---------- Authentication ----------

def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> str:
    now = datetime.now(timezone.utc)
    if credentials is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    expiry = _tokens.get(credentials.credentials)
    if expiry is None or expiry < now:
        _tokens.pop(credentials.credentials, None)
        raise HTTPException(status_code=401, detail="unauthorized")
    return CLIENT_ID


COMMON_ERRORS = {
    401: {"model": ErrorResponse, "description": "Missing, invalid or expired token."},
    422: {"model": ErrorResponse, "description": "Validation error."},
}


# ---------- Dashboard ----------

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC_DIR / "dashboard.html", media_type="text/html")


# ---------- Health ----------

@app.get(
    "/api/v1/health",
    tags=["Health"],
    summary="Check service health",
    response_model=HealthResponse,
)
def health():
    return {"status": "ok", "version": API_VERSION, "time": datetime.now(timezone.utc)}


# ---------- Authentication ----------

@app.post(
    "/api/v1/auth/token",
    tags=["Authentication"],
    summary="Get an access token",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Incorrect credentials."},
        422: {"model": ErrorResponse, "description": "Validation error."},
    },
)
def create_token(body: TokenRequest):
    if not (
        secrets.compare_digest(body.client_id, CLIENT_ID)
        and secrets.compare_digest(body.client_secret, CLIENT_SECRET)
    ):
        raise HTTPException(status_code=401, detail="invalid_credentials")
    token = secrets.token_urlsafe(32)
    _tokens[token] = datetime.now(timezone.utc) + timedelta(seconds=TOKEN_TTL_SECONDS)
    return TokenResponse(access_token=token, expires_in=TOKEN_TTL_SECONDS)


# ---------- Devices ----------

@app.get(
    "/api/v1/devices",
    tags=["Devices"],
    summary="List devices",
    response_model=DeviceList,
    responses=COMMON_ERRORS,
)
def list_devices(
    _: str = Depends(require_auth),
    device_status: Optional[DeviceStatus] = Query(None, alias="status"),
    site: Optional[str] = Query(None, description="Exact site name."),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    items = list(store.devices.values())
    if device_status:
        items = [d for d in items if d["status"] == device_status.value]
    if site:
        items = [d for d in items if d["site"] == site]
    total = len(items)
    return DeviceList(items=items[offset : offset + limit], total=total, limit=limit, offset=offset)


@app.post(
    "/api/v1/devices",
    tags=["Devices"],
    summary="Register a device",
    response_model=Device,
    status_code=status.HTTP_201_CREATED,
    responses=COMMON_ERRORS,
)
def create_device(body: DeviceCreate, _: str = Depends(require_auth)):
    dev_id = store.next_device_id()
    device = {
        "id": dev_id,
        **body.model_dump(mode="json"),
        "status": "offline",
        "last_seen": None,
        "created_at": datetime.now(timezone.utc),
    }
    store.devices[dev_id] = device
    store.telemetry[dev_id] = []
    return device


def _get_device_or_404(device_id: str) -> dict:
    device = store.devices.get(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device_not_found")
    return device


@app.get(
    "/api/v1/devices/{device_id}",
    tags=["Devices"],
    summary="Get a device",
    response_model=Device,
    responses={**COMMON_ERRORS, 404: {"model": ErrorResponse, "description": "Device not found."}},
)
def get_device(device_id: str, _: str = Depends(require_auth)):
    return _get_device_or_404(device_id)


@app.patch(
    "/api/v1/devices/{device_id}",
    tags=["Devices"],
    summary="Update a device",
    response_model=Device,
    responses={**COMMON_ERRORS, 404: {"model": ErrorResponse, "description": "Device not found."}},
)
def update_device(device_id: str, body: DeviceUpdate, _: str = Depends(require_auth)):
    device = _get_device_or_404(device_id)
    device.update(body.model_dump(mode="json", exclude_none=True))
    return device


@app.delete(
    "/api/v1/devices/{device_id}",
    tags=["Devices"],
    summary="Delete a device",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**COMMON_ERRORS, 404: {"model": ErrorResponse, "description": "Device not found."}},
)
def delete_device(device_id: str, _: str = Depends(require_auth)):
    _get_device_or_404(device_id)
    del store.devices[device_id]
    store.telemetry.pop(device_id, None)
    for alert_id in [a for a, v in store.alerts.items() if v["device_id"] == device_id]:
        del store.alerts[alert_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- Telemetry ----------

@app.get(
    "/api/v1/devices/{device_id}/telemetry",
    tags=["Telemetry"],
    summary="List telemetry readings",
    response_model=TelemetryList,
    responses={**COMMON_ERRORS, 404: {"model": ErrorResponse, "description": "Device not found."}},
)
def list_telemetry(
    device_id: str,
    _: str = Depends(require_auth),
    since: Optional[datetime] = Query(None, description="Return readings at or after this UTC time."),
    limit: int = Query(10, ge=1, le=100, description="Maximum readings, newest first."),
):
    _get_device_or_404(device_id)
    readings = store.telemetry.get(device_id, [])
    if since:
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)
        readings = [r for r in readings if r["timestamp"] >= since]
    newest_first = sorted(readings, key=lambda r: r["timestamp"], reverse=True)[:limit]
    return TelemetryList(device_id=device_id, items=newest_first, count=len(newest_first))


@app.post(
    "/api/v1/devices/{device_id}/telemetry",
    tags=["Telemetry"],
    summary="Submit a telemetry reading",
    description=(
        "Stores one reading and marks the device online. If vibration exceeds "
        f"{VIBRATION_ALERT_LIMIT_MM_S} mm/s, a critical alert is raised automatically."
    ),
    response_model=TelemetryReading,
    status_code=status.HTTP_201_CREATED,
    responses={**COMMON_ERRORS, 404: {"model": ErrorResponse, "description": "Device not found."}},
)
def submit_telemetry(device_id: str, body: TelemetryCreate, _: str = Depends(require_auth)):
    device = _get_device_or_404(device_id)
    now = datetime.now(timezone.utc)
    reading = {**body.model_dump(), "device_id": device_id, "timestamp": body.timestamp or now}
    store.telemetry.setdefault(device_id, []).append(reading)
    device["last_seen"] = now
    if device["status"] == "offline":
        device["status"] = "online"
    if body.vibration_mm_s > VIBRATION_ALERT_LIMIT_MM_S:
        alert_id = store.next_alert_id()
        store.alerts[alert_id] = {
            "id": alert_id,
            "device_id": device_id,
            "severity": Severity.critical.value,
            "state": AlertState.open.value,
            "message": (
                f"Vibration {body.vibration_mm_s} mm/s exceeds the "
                f"{VIBRATION_ALERT_LIMIT_MM_S} mm/s limit."
            ),
            "raised_at": now,
            "acknowledged_at": None,
            "acknowledged_by": None,
        }
    return reading


# ---------- Alerts ----------

@app.get(
    "/api/v1/alerts",
    tags=["Alerts"],
    summary="List alerts",
    response_model=AlertList,
    responses=COMMON_ERRORS,
)
def list_alerts(
    _: str = Depends(require_auth),
    severity: Optional[Severity] = None,
    state: Optional[AlertState] = None,
    device_id: Optional[str] = None,
):
    items = list(store.alerts.values())
    if severity:
        items = [a for a in items if a["severity"] == severity.value]
    if state:
        items = [a for a in items if a["state"] == state.value]
    if device_id:
        items = [a for a in items if a["device_id"] == device_id]
    items.sort(key=lambda a: a["raised_at"], reverse=True)
    return AlertList(items=items, total=len(items))


@app.post(
    "/api/v1/alerts/{alert_id}/acknowledge",
    tags=["Alerts"],
    summary="Acknowledge an alert",
    response_model=Alert,
    responses={
        **COMMON_ERRORS,
        404: {"model": ErrorResponse, "description": "Alert not found."},
        409: {"model": ErrorResponse, "description": "Alert already acknowledged."},
    },
)
def acknowledge_alert(alert_id: str, client: str = Depends(require_auth)):
    alert = store.alerts.get(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="alert_not_found")
    if alert["state"] == AlertState.acknowledged.value:
        raise HTTPException(status_code=409, detail="alert_already_acknowledged")
    alert.update(
        state=AlertState.acknowledged.value,
        acknowledged_at=datetime.now(timezone.utc),
        acknowledged_by=client,
    )
    return alert
