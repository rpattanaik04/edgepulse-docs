"""Pydantic models for the EdgePulse demo API."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DeviceStatus(str, Enum):
    online = "online"
    offline = "offline"
    maintenance = "maintenance"


class Protocol(str, Enum):
    mqtt = "mqtt"
    opcua = "opcua"
    modbus = "modbus"


class Severity(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class AlertState(str, Enum):
    open = "open"
    acknowledged = "acknowledged"


# ---------- Health ----------

class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])
    version: str = Field(..., examples=["1.2.0"])
    time: datetime = Field(..., description="Server time in UTC.")


# ---------- Authentication ----------

class TokenRequest(BaseModel):
    client_id: str = Field(..., examples=["demo-client"])
    client_secret: str = Field(..., examples=["demo-secret"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(..., description="Token lifetime in seconds.")


# ---------- Devices ----------

class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=64, examples=["Boiler Gateway 07"])
    site: str = Field(..., min_length=2, max_length=64, examples=["Pune Plant"])
    protocol: Protocol = Protocol.mqtt
    firmware: str = Field("1.0.0", examples=["1.2.4"])


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=64)
    site: Optional[str] = Field(None, min_length=2, max_length=64)
    status: Optional[DeviceStatus] = None
    firmware: Optional[str] = None


class Device(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(..., examples=["dev_1001"])
    name: str
    site: str
    protocol: Protocol
    status: DeviceStatus
    firmware: str
    last_seen: Optional[datetime] = None
    created_at: datetime


class DeviceList(BaseModel):
    items: list[Device]
    total: int
    limit: int
    offset: int


# ---------- Telemetry ----------

class TelemetryCreate(BaseModel):
    temperature_c: float = Field(..., ge=-50, le=200, examples=[72.4])
    vibration_mm_s: float = Field(..., ge=0, le=100, examples=[2.1])
    pressure_kpa: float = Field(..., ge=0, le=2000, examples=[412.0])
    timestamp: Optional[datetime] = Field(
        None, description="Reading time in UTC. Defaults to server time."
    )


class TelemetryReading(TelemetryCreate):
    device_id: str
    timestamp: datetime


class TelemetryList(BaseModel):
    device_id: str
    items: list[TelemetryReading]
    count: int


# ---------- Alerts ----------

class Alert(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(..., examples=["alt_5001"])
    device_id: str
    severity: Severity
    state: AlertState
    message: str
    raised_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None


class AlertList(BaseModel):
    items: list[Alert]
    total: int


# ---------- Errors ----------

class ErrorDetail(BaseModel):
    field: str = Field(..., examples=["name"])
    issue: str = Field(..., examples=["String should have at least 3 characters"])


class ErrorBody(BaseModel):
    code: str = Field(..., description="Stable, machine-readable error code.")
    message: str = Field(..., description="Readable explanation of the error.")
    details: Optional[list[ErrorDetail]] = Field(
        None, description="Present for validation errors. One item per invalid field."
    )


class ErrorResponse(BaseModel):
    error: ErrorBody
