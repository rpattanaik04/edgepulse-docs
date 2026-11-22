"""In-memory data store with fictional seed data.

All names, sites and readings are fictional. Data resets when the server restarts.
"""

import itertools
import random
from datetime import datetime, timedelta, timezone

NOW = lambda: datetime.now(timezone.utc)  # noqa: E731

_device_seq = itertools.count(1006)
_alert_seq = itertools.count(5004)

devices: dict[str, dict] = {}
telemetry: dict[str, list[dict]] = {}
alerts: dict[str, dict] = {}


def next_device_id() -> str:
    return f"dev_{next(_device_seq)}"


def next_alert_id() -> str:
    return f"alt_{next(_alert_seq)}"


def seed() -> None:
    """Load the fictional demo dataset."""
    devices.clear()
    telemetry.clear()
    alerts.clear()

    rng = random.Random(42)  # fixed seed so documented examples stay stable
    now = NOW()

    seed_devices = [
        ("dev_1001", "Boiler Gateway 01", "Pune Plant", "mqtt", "online", "1.2.4"),
        ("dev_1002", "Compressor Sensor 02", "Pune Plant", "modbus", "online", "1.2.4"),
        ("dev_1003", "Turbine Monitor 03", "Hosur Plant", "opcua", "online", "1.2.0"),
        ("dev_1004", "Pump Controller 04", "Hosur Plant", "modbus", "maintenance", "1.1.9"),
        ("dev_1005", "Cooling Unit Gateway 05", "Pune Plant", "mqtt", "offline", "1.1.9"),
    ]
    for dev_id, name, site, protocol, status, firmware in seed_devices:
        devices[dev_id] = {
            "id": dev_id,
            "name": name,
            "site": site,
            "protocol": protocol,
            "status": status,
            "firmware": firmware,
            "last_seen": None if status == "offline" else now,
            "created_at": now - timedelta(days=90),
        }
        readings = []
        for i in range(24):
            readings.append(
                {
                    "device_id": dev_id,
                    "timestamp": now - timedelta(minutes=5 * (24 - i)),
                    "temperature_c": round(rng.uniform(60, 80), 1),
                    "vibration_mm_s": round(rng.uniform(1.0, 3.5), 1),
                    "pressure_kpa": round(rng.uniform(380, 440), 1),
                }
            )
        telemetry[dev_id] = readings

    seed_alerts = [
        ("alt_5001", "dev_1003", "critical", "open",
         "Vibration 6.8 mm/s exceeds the 5.0 mm/s limit."),
        ("alt_5002", "dev_1005", "warning", "open",
         "Device has not reported for 15 minutes."),
        ("alt_5003", "dev_1001", "info", "acknowledged",
         "Firmware 1.2.4 installed successfully."),
    ]
    for alert_id, dev_id, severity, state, message in seed_alerts:
        alerts[alert_id] = {
            "id": alert_id,
            "device_id": dev_id,
            "severity": severity,
            "state": state,
            "message": message,
            "raised_at": now - timedelta(hours=2),
            "acknowledged_at": now - timedelta(hours=1) if state == "acknowledged" else None,
            "acknowledged_by": "demo-client" if state == "acknowledged" else None,
        }


seed()
