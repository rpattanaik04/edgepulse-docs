# Developer guide

- **Audience:** Developers who build applications and scripts on the EdgePulse API.
- **Document type:** Developer guide with tutorials
- **Applies to:** EdgePulse API 1.2.0
- **Last updated:** 2026-11-20

## Overview

This guide teaches you to work with the EdgePulse API through three tested tutorials: monitor devices and alerts, simulate a device, and page through results. It also provides a reusable Python client that handles authentication for you.

## Purpose

After you complete the tutorials, you can:

- Authenticate once and recover automatically when a token expires.
- Read devices and alerts, including paged results.
- Send telemetry and observe the alert that it raises.
- Handle API errors by their code.

## Prerequisites

- A running EdgePulse API. See the [quick start](../quick-start/index.md).
- Python 3.10 or later with the `requests` package: `pip install requests`.
- Node.js 18 or later, for tutorial 3.
- The `examples` folder from the repository. All code in this guide is stored there and was tested.

!!! tip "Start from clean data"
    Restart the API before tutorial 1. The outputs in this guide come from running the tutorials in order, on fresh demo data. If you run them in another order, some values differ.

## Key concepts

| Concept | What to know |
|---|---|
| **Base URL** | `http://localhost:8000` for a local installation. Set `EDGEPULSE_URL` to use another address. |
| **Token** | Valid for 3600 seconds. See the [authentication guide](../api/authentication.md). |
| **Paging** | List endpoints use `limit` and `offset`. The response `total` is the number of matching items. |
| **Errors** | Every error is JSON with `error.code`, `error.message` and, for validation errors, `error.details`. |
| **Timestamps** | ISO 8601 in UTC, for example `2026-11-20T05:48:34Z`. |

## A reusable client

The tutorials share one small client. It gets a token when it needs one, gets a new token if the old one expired, raises a typed error when the API returns an error, and pages through list results.

Save this code as `examples/python/edgepulse_client.py`.

```python
"""A minimal EdgePulse API client that handles access tokens for you."""

import os

import requests


class EdgePulseError(Exception):
    """Raised when the API returns an error response."""

    def __init__(self, status, code, message, details=None):
        super().__init__(f"{status} {code}: {message}")
        self.status = status
        self.code = code
        self.message = message
        self.details = details or []


class EdgePulseClient:
    def __init__(self, base_url=None, client_id=None, client_secret=None):
        self.base_url = (base_url or os.getenv("EDGEPULSE_URL", "http://localhost:8000")).rstrip("/")
        self.client_id = client_id or os.getenv("EDGEPULSE_CLIENT_ID", "demo-client")
        self.client_secret = client_secret or os.getenv("EDGEPULSE_CLIENT_SECRET", "demo-secret")
        self._token = None
        self._session = requests.Session()

    def _send(self, method, path, use_token=True, **kwargs):
        headers = {"Authorization": f"Bearer {self._token}"} if use_token and self._token else {}
        # A long timeout allows a free-tier host to wake up after being idle.
        response = self._session.request(
            method, self.base_url + path, headers=headers, timeout=90, **kwargs
        )
        if response.status_code == 204:
            return None
        body = response.json()
        if not response.ok:
            error = body["error"]
            raise EdgePulseError(response.status_code, error["code"], error["message"], error.get("details"))
        return body

    def _authenticate(self):
        body = {"client_id": self.client_id, "client_secret": self.client_secret}
        self._token = self._send("POST", "/api/v1/auth/token", use_token=False, json=body)["access_token"]

    def request(self, method, path, **kwargs):
        """Send a request. Gets a token first, and gets a new one if the token expired."""
        if self._token is None:
            self._authenticate()
        try:
            return self._send(method, path, **kwargs)
        except EdgePulseError as error:
            if error.code != "unauthorized":
                raise
            self._authenticate()  # The token expired. Get a new one and retry once.
            return self._send(method, path, **kwargs)

    def pages(self, path, params=None, page_size=100):
        """Yield every item from a paged list endpoint."""
        offset = 0
        while True:
            query = {**(params or {}), "limit": page_size, "offset": offset}
            page = self.request("GET", path, params=query)
            yield from page["items"]
            offset += page_size
            if offset >= page["total"]:
                break
```

The client reads its settings from environment variables, so the same code works against a local or a hosted API: `EDGEPULSE_URL`, `EDGEPULSE_CLIENT_ID` and `EDGEPULSE_CLIENT_SECRET`.

## Tutorial 1: Find devices and alerts that need attention

**Goal:** List every device that is not online, and every alert that nobody has acknowledged.

Save this code as `examples/python/list_problem_devices.py`.

```python
"""List devices that need attention and alerts that nobody has acknowledged."""

from edgepulse_client import EdgePulseClient

client = EdgePulseClient()

devices = [d for d in client.pages("/api/v1/devices") if d["status"] != "online"]
print(f"Devices that need attention ({len(devices)}):")
for device in devices:
    print(f"  {device['id']}  {device['name']:<26} {device['status']}")

alerts = client.request("GET", "/api/v1/alerts", params={"state": "open"})
print(f"Open alerts ({alerts['total']}):")
for alert in alerts["items"]:
    print(f"  {alert['severity']:<9} {alert['device_id']}  {alert['message']}")
```

Run it from the `examples/python` folder:

```bash
python list_problem_devices.py
```

**Expected result:**

```text
Devices that need attention (2):
  dev_1004  Pump Controller 04         maintenance
  dev_1005  Cooling Unit Gateway 05    offline
Open alerts (2):
  critical  dev_1003  Vibration 6.8 mm/s exceeds the 5.0 mm/s limit.
  warning   dev_1005  Device has not reported for 15 minutes.
```

**What happened:** `pages` requested the devices in pages of 100 and returned them one by one. The script kept the devices whose status is not `online`. A second request used the `state=open` filter to fetch only open alerts.

## Tutorial 2: Simulate a device that raises an alert

**Goal:** Send six readings for a device, the last one above the vibration limit, and confirm that the API raises a critical alert.

![Sequence diagram. A device or script posts a telemetry reading with vibration of 6.4 millimeters per second. The API stores the reading, sets the device online, and raises a critical alert, and then returns 201 Created. An operator lists open alerts and receives the new alert, and then acknowledges it.](../assets/diagrams/exports/telemetry-alert-flow.png)

*Figure 1. From a telemetry reading to an acknowledged alert.*

Save this code as `examples/python/simulate_device.py`.

```python
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
```

Run it. You can pass another device ID as an argument.

```bash
python simulate_device.py
```

**Expected result:**

```text
Sent 6 readings to dev_1005.
Device status: online
Critical alerts for dev_1005: 0 before, 1 after
```

**What happened:** The device `dev_1005` started as `offline`. Its first reading set it to `online`. The last reading had vibration of 6.1 mm/s, above 5.0, so the API raised one critical alert. Open the dashboard and select **Refresh** to see the alert.

## Tutorial 3: Page through devices in JavaScript

**Goal:** Read all devices two at a time to understand `limit`, `offset` and `total`.

Save this code as `examples/node/list_devices.mjs`.

```javascript
// Page through all devices, two at a time, to show how limit and offset work.
const BASE_URL = "http://localhost:8000";
const PAGE_SIZE = 2;

const { access_token } = await (
  await fetch(`${BASE_URL}/api/v1/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ client_id: "demo-client", client_secret: "demo-secret" }),
  })
).json();

let offset = 0;
let total = Infinity;
while (offset < total) {
  const response = await fetch(`${BASE_URL}/api/v1/devices?limit=${PAGE_SIZE}&offset=${offset}`, {
    headers: { Authorization: `Bearer ${access_token}` },
  });
  const page = await response.json();
  total = page.total;
  console.log(`Page ${offset / PAGE_SIZE + 1} (offset ${offset}):`);
  for (const device of page.items) {
    console.log(`  ${device.id}  ${device.name}  [${device.status}]`);
  }
  offset += PAGE_SIZE;
}
console.log(`Done. ${total} devices.`);
```

Run it from the `examples/node` folder:

```bash
node list_devices.mjs
```

**Expected result:** `dev_1005` shows `online` because tutorial 2 sent it readings.

```text
Page 1 (offset 0):
  dev_1001  Boiler Gateway 01  [online]
  dev_1002  Compressor Sensor 02  [online]
Page 2 (offset 2):
  dev_1003  Turbine Monitor 03  [online]
  dev_1004  Pump Controller 04  [maintenance]
Page 3 (offset 4):
  dev_1005  Cooling Unit Gateway 05  [online]
Done. 5 devices.
```

**What happened:** The loop requested two devices at a time and advanced `offset` by two. It stopped when `offset` reached `total`, which the first response reported as 5.

## Handle errors

Check `error.code`, not the message text. Codes are stable, and messages can change.

```python
from edgepulse_client import EdgePulseClient, EdgePulseError

client = EdgePulseClient()
try:
    client.request("GET", "/api/v1/devices/dev_9999")
except EdgePulseError as error:
    print(error.status, error.code)   # 404 device_not_found
```

The full list of codes is in the [API reference](../api/reference.md#error-codes).

## Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| `ModuleNotFoundError: No module named 'edgepulse_client'` | You ran the script from another folder. | Run it from `examples/python`. |
| `ModuleNotFoundError: No module named 'requests'` | The package is not installed. | Run `pip install requests`. |
| `ConnectionError` or `ECONNREFUSED` | The API is not running, or the address is wrong. | Start the API. Set `EDGEPULSE_URL` if you use another address. |
| `EdgePulseError: 401 invalid_credentials` | The credentials do not match the server. | Set `EDGEPULSE_CLIENT_ID` and `EDGEPULSE_CLIENT_SECRET`. |
| `EdgePulseError: 404 device_not_found` | The device ID does not exist. | List devices and use an existing ID. |
| Different output from this guide | The data changed during earlier runs. | Restart the API to reset the data. |

## Best practices

- Reuse one client for many requests, so that the token is reused.
- Filter on the server with query parameters instead of downloading everything.
- Use a page size of 100 or less, because 100 is the maximum.
- Branch on `error.code`.
- Send timestamps in UTC.

## Related information

- [API reference](../api/reference.md)
- [Authentication guide](../api/authentication.md)
- [Product overview](../overview/index.md)
