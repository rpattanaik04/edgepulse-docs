"""Simulate a device that sends readings, ending with a vibration spike."""

import sys

from edgepulse_client import EdgePulseClient

DEVICE_ID = sys.argv[1] if len(sys.argv) > 1 else "dev_1005"

# Temperature (°C), vibration (mm/s), pressure (kPa). The last reading is above the vibration limit.
READINGS = [
    (70.1, 2.0, 402.0),
    (70.8, 2.2, 405.5),
    (71.4, 2.1, 404.0),
    (72.0, 2.6, 407.2),
    (72.9, 3.1, 409.8),
    (74.3, 6.1, 411.0),
]

client = EdgePulseClient()
before = client.request("GET", "/api/v1/alerts", params={"device_id": DEVICE_ID, "severity": "critical"})["total"]

for temperature, vibration, pressure in READINGS:
    client.request(
        "POST",
        f"/api/v1/devices/{DEVICE_ID}/telemetry",
        json={"temperature_c": temperature, "vibration_mm_s": vibration, "pressure_kpa": pressure},
    )

device = client.request("GET", f"/api/v1/devices/{DEVICE_ID}")
after = client.request("GET", "/api/v1/alerts", params={"device_id": DEVICE_ID, "severity": "critical"})["total"]

print(f"Sent {len(READINGS)} readings to {DEVICE_ID}.")
print(f"Device status: {device['status']}")
print(f"Critical alerts for {DEVICE_ID}: {before} before, {after} after")
