# EdgePulse API reference

- **Audience:** Developers and integrators who call the EdgePulse REST API.
- **Document type:** API reference
- **Applies to:** EdgePulse API 1.2.0
- **Last updated:** 2026-11-20
- **Tested on:** 2026-11-20, against a running instance of the API

!!! note "Every JSON example on this page is real output"
    Each request in this document was run against the working demo API, and the response shown is the one the API returned. A test script checked every status code. The results are in [Test results](#test-results). Two values differ from the raw output: the access token is replaced by `<access_token>`, and timestamps reflect the moment of testing.

## Overview

The EdgePulse API is a REST API that uses JSON. It lets you register devices, send and read telemetry, and list and acknowledge alerts.

## Prerequisites

- A running instance of the demo API. See [api-demo/README.md](https://github.com/rpattanaik04/edgepulse-docs/tree/main/api-demo).
- `curl`, or any HTTP client.
- The demo credentials: `client_id` = `demo-client`, `client_secret` = `demo-secret`.

!!! tip "Hosted copies may start slowly"
    If the API runs on a free hosting tier that sleeps when idle, the first request after a quiet period can take about one minute. Demo data resets each time the service restarts.

## Conventions

| Item | Value |
|---|---|
| Base URL | `http://localhost:8000` when you run the API locally |
| Version prefix | `/api/v1` |
| Format | JSON for all requests and responses |
| Authentication | Bearer token in the `Authorization` header, on every endpoint except `health` and `auth/token` |
| Timestamps | ISO 8601, in UTC |
| Token lifetime | 3600 seconds. There is no refresh. Request a new token when it expires. |

The examples use `http://localhost:8000`. Replace it with the address of your instance.

### Standard error format

Every error returns the same structure.

| Field | Type | Description |
|---|---|---|
| `error.code` | string | A stable, machine-readable code. |
| `error.message` | string | A readable explanation. |
| `error.details` | array | Optional. Present for validation errors. Each item has `field` and `issue`. |

### Status codes

| Code | Meaning |
|---|---|
| 200 | The request succeeded. |
| 201 | A resource was created. |
| 204 | The request succeeded and there is no response body. |
| 401 | The token is missing, invalid or expired, or the credentials are wrong. |
| 404 | The device or alert does not exist. |
| 409 | The request conflicts with the current state of the resource. |
| 422 | The request contains invalid data. |

## Health

### Check service health

`GET /api/v1/health`

Returns the service status and version. Requires no token. Use it to confirm that the API is running.

**Request**

```bash
curl http://localhost:8000/api/v1/health
```

**Response:** `200 OK`

```json
{
    "status": "ok",
    "version": "1.2.0",
    "time": "2026-11-20T05:46:56.887749Z"
}
```

## Authentication

### Get an access token

`POST /api/v1/auth/token`

Exchanges client credentials for a bearer token. Requires no token.

**Request body**

| Field | Type | Required | Description |
|---|---|---|---|
| `client_id` | string | Yes | Your client ID. |
| `client_secret` | string | Yes | Your client secret. |

**Request**

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "demo-client",
    "client_secret": "demo-secret"
  }'
```

**Response:** `200 OK`

```json
{
    "access_token": "<access_token>",
    "token_type": "Bearer",
    "expires_in": 3600
}
```

| Field | Type | Description |
|---|---|---|
| `access_token` | string | The token to send with each request. |
| `token_type` | string | Always `Bearer`. |
| `expires_in` | integer | Lifetime in seconds. |

**Error: wrong credentials**

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "demo-client",
    "client_secret": "wrong-secret"
  }'
```

**Response:** `401 Unauthorized`

```json
{
    "error": {
        "code": "invalid_credentials",
        "message": "The client ID or client secret is incorrect."
    }
}
```

**Error: missing token on a protected endpoint**

```bash
curl http://localhost:8000/api/v1/devices
```

**Response:** `401 Unauthorized`

```json
{
    "error": {
        "code": "unauthorized",
        "message": "Missing, invalid or expired access token."
    }
}
```

## Devices

A device object has these fields.

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique ID, such as `dev_1001`. |
| `name` | string | Device name. |
| `site` | string | Site where the device is installed. |
| `protocol` | string | `mqtt`, `opcua` or `modbus`. |
| `status` | string | `online`, `offline` or `maintenance`. |
| `firmware` | string | Installed firmware version. |
| `last_seen` | string or null | Time of the last reading. `null` if the device has never reported. |
| `created_at` | string | Time the device was registered. |

### List devices

`GET /api/v1/devices`

Returns a page of devices.

**Query parameters**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `status` | string | No | None | Filter by `online`, `offline` or `maintenance`. |
| `site` | string | No | None | Filter by exact site name. |
| `limit` | integer | No | 20 | Page size, from 1 to 100. |
| `offset` | integer | No | 0 | Number of devices to skip. |

**Request**

```bash
curl "http://localhost:8000/api/v1/devices?status=online&limit=2" \
  -H "Authorization: Bearer <access_token>"
```

**Response:** `200 OK`

```json
{
    "items": [
        {
            "id": "dev_1001",
            "name": "Boiler Gateway 01",
            "site": "Pune Plant",
            "protocol": "mqtt",
            "status": "online",
            "firmware": "1.2.4",
            "last_seen": "2026-11-20T05:46:54.013778Z",
            "created_at": "2026-08-22T05:46:54.013778Z"
        },
        {
            "id": "dev_1002",
            "name": "Compressor Sensor 02",
            "site": "Pune Plant",
            "protocol": "modbus",
            "status": "online",
            "firmware": "1.2.4",
            "last_seen": "2026-11-20T05:46:54.013778Z",
            "created_at": "2026-08-22T05:46:54.013778Z"
        }
    ],
    "total": 3,
    "limit": 2,
    "offset": 0
}
```

`total` is the number of devices that match the filters, not the number on the page.

### Get a device

`GET /api/v1/devices/{device_id}`

**Request**

```bash
curl http://localhost:8000/api/v1/devices/dev_1001 \
  -H "Authorization: Bearer <access_token>"
```

**Response:** `200 OK`

```json
{
    "id": "dev_1001",
    "name": "Boiler Gateway 01",
    "site": "Pune Plant",
    "protocol": "mqtt",
    "status": "online",
    "firmware": "1.2.4",
    "last_seen": "2026-11-20T05:46:54.013778Z",
    "created_at": "2026-08-22T05:46:54.013778Z"
}
```

**Error: device not found**

```bash
curl http://localhost:8000/api/v1/devices/dev_9999 \
  -H "Authorization: Bearer <access_token>"
```

**Response:** `404 Not Found`

```json
{
    "error": {
        "code": "device_not_found",
        "message": "No device exists with the given ID."
    }
}
```

### Register a device

`POST /api/v1/devices`

Creates a device. The new device starts with the status `offline` and becomes `online` when it sends its first reading.

**Request body**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | 3 to 64 characters. |
| `site` | string | Yes | 2 to 64 characters. |
| `protocol` | string | No | `mqtt` (default), `opcua` or `modbus`. |
| `firmware` | string | No | Default `1.0.0`. |

**Request**

```bash
curl -X POST http://localhost:8000/api/v1/devices \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Chiller Gateway 06",
    "site": "Pune Plant",
    "protocol": "mqtt",
    "firmware": "1.2.4"
  }'
```

**Response:** `201 Created`

```json
{
    "id": "dev_1006",
    "name": "Chiller Gateway 06",
    "site": "Pune Plant",
    "protocol": "mqtt",
    "status": "offline",
    "firmware": "1.2.4",
    "last_seen": null,
    "created_at": "2026-11-20T05:46:56.902926Z"
}
```

**Error: invalid data**

```bash
curl -X POST http://localhost:8000/api/v1/devices \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "x",
    "site": "P"
  }'
```

**Response:** `422 Unprocessable Content`

```json
{
    "error": {
        "code": "validation_error",
        "message": "The request contains invalid data.",
        "details": [
            {
                "field": "name",
                "issue": "String should have at least 3 characters"
            },
            {
                "field": "site",
                "issue": "String should have at least 2 characters"
            }
        ]
    }
}
```

### Update a device

`PATCH /api/v1/devices/{device_id}`

Changes only the fields you send. All fields are optional: `name`, `site`, `status`, `firmware`.

**Request**

```bash
curl -X PATCH http://localhost:8000/api/v1/devices/dev_1006 \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "maintenance"
  }'
```

**Response:** `200 OK`

```json
{
    "id": "dev_1006",
    "name": "Chiller Gateway 06",
    "site": "Pune Plant",
    "protocol": "mqtt",
    "status": "maintenance",
    "firmware": "1.2.4",
    "last_seen": null,
    "created_at": "2026-11-20T05:46:56.902926Z"
}
```

### Delete a device

`DELETE /api/v1/devices/{device_id}`

Deletes the device together with its readings and alerts.

!!! warning
    Deletion cannot be undone.

**Request**

```bash
curl -X DELETE http://localhost:8000/api/v1/devices/dev_1006 \
  -H "Authorization: Bearer <access_token>"
```

**Response:** `204 No Content`

The response has no body.

## Telemetry

A reading has these fields.

| Field | Type | Range | Description |
|---|---|---|---|
| `device_id` | string | | The device that sent the reading. |
| `timestamp` | string | | Time of the reading. Defaults to server time. |
| `temperature_c` | number | -50 to 200 | Temperature in °C. |
| `vibration_mm_s` | number | 0 to 100 | Vibration in mm/s. |
| `pressure_kpa` | number | 0 to 2000 | Pressure in kPa. |

### List telemetry readings

`GET /api/v1/devices/{device_id}/telemetry`

Returns readings, newest first.

**Query parameters**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `since` | string | No | None | Return readings at or after this UTC time. |
| `limit` | integer | No | 10 | Maximum readings, from 1 to 100. |

**Request**

```bash
curl "http://localhost:8000/api/v1/devices/dev_1001/telemetry?limit=2" \
  -H "Authorization: Bearer <access_token>"
```

**Response:** `200 OK`

```json
{
    "device_id": "dev_1001",
    "items": [
        {
            "temperature_c": 65.4,
            "vibration_mm_s": 1.5,
            "pressure_kpa": 436.6,
            "timestamp": "2026-11-20T05:41:54.013778Z",
            "device_id": "dev_1001"
        },
        {
            "temperature_c": 64.6,
            "vibration_mm_s": 1.1,
            "pressure_kpa": 398.9,
            "timestamp": "2026-11-20T05:36:54.013778Z",
            "device_id": "dev_1001"
        }
    ],
    "count": 2
}
```

### Submit a telemetry reading

`POST /api/v1/devices/{device_id}/telemetry`

Stores one reading. The device `last_seen` time is updated, and an `offline` device becomes `online`.

!!! note "Automatic alert"
    If `vibration_mm_s` is greater than 5.0, the API raises a critical alert.

**Request body.** Send `temperature_c`, `vibration_mm_s` and `pressure_kpa`. `timestamp` is optional.

**Request**

```bash
curl -X POST http://localhost:8000/api/v1/devices/dev_1005/telemetry \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "temperature_c": 71.5,
    "vibration_mm_s": 2.3,
    "pressure_kpa": 405.0
  }'
```

**Response:** `201 Created`

```json
{
    "temperature_c": 71.5,
    "vibration_mm_s": 2.3,
    "pressure_kpa": 405.0,
    "timestamp": "2026-11-20T05:46:56.913566Z",
    "device_id": "dev_1005"
}
```

**Result: the device is now online**

```bash
curl http://localhost:8000/api/v1/devices/dev_1005 \
  -H "Authorization: Bearer <access_token>"
```

**Response:** `200 OK`

```json
{
    "id": "dev_1005",
    "name": "Cooling Unit Gateway 05",
    "site": "Pune Plant",
    "protocol": "mqtt",
    "status": "online",
    "firmware": "1.1.9",
    "last_seen": "2026-11-20T05:46:56.913566Z",
    "created_at": "2026-08-22T05:46:54.013778Z"
}
```

**Example: a reading above the vibration limit**

```bash
curl -X POST http://localhost:8000/api/v1/devices/dev_1001/telemetry \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "temperature_c": 78.2,
    "vibration_mm_s": 6.4,
    "pressure_kpa": 421.0
  }'
```

**Response:** `201 Created`

```json
{
    "temperature_c": 78.2,
    "vibration_mm_s": 6.4,
    "pressure_kpa": 421.0,
    "timestamp": "2026-11-20T05:46:56.916933Z",
    "device_id": "dev_1001"
}
```

## Alerts

An alert object has these fields.

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique ID, such as `alt_5001`. |
| `device_id` | string | The device that raised the alert. |
| `severity` | string | `info`, `warning` or `critical`. |
| `state` | string | `open` or `acknowledged`. |
| `message` | string | A readable description. |
| `raised_at` | string | Time the alert was raised. |
| `acknowledged_at` | string or null | Time of acknowledgement. |
| `acknowledged_by` | string or null | Client ID that acknowledged the alert. |

### List alerts

`GET /api/v1/alerts`

Returns alerts, newest first.

**Query parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `severity` | string | No | `info`, `warning` or `critical`. |
| `state` | string | No | `open` or `acknowledged`. |
| `device_id` | string | No | Only alerts for this device. |

**Request**

```bash
curl "http://localhost:8000/api/v1/alerts?severity=critical&state=open" \
  -H "Authorization: Bearer <access_token>"
```

**Response:** `200 OK`

```json
{
    "items": [
        {
            "id": "alt_5004",
            "device_id": "dev_1001",
            "severity": "critical",
            "state": "open",
            "message": "Vibration 6.4 mm/s exceeds the 5.0 mm/s limit.",
            "raised_at": "2026-11-20T05:46:56.916933Z",
            "acknowledged_at": null,
            "acknowledged_by": null
        },
        {
            "id": "alt_5001",
            "device_id": "dev_1003",
            "severity": "critical",
            "state": "open",
            "message": "Vibration 6.8 mm/s exceeds the 5.0 mm/s limit.",
            "raised_at": "2026-11-20T03:46:54.013778Z",
            "acknowledged_at": null,
            "acknowledged_by": null
        }
    ],
    "total": 2
}
```

The first item is the alert raised by the high-vibration reading submitted earlier.

### Acknowledge an alert

`POST /api/v1/alerts/{alert_id}/acknowledge`

Marks an open alert as acknowledged and records who acknowledged it and when.

**Request**

```bash
curl -X POST http://localhost:8000/api/v1/alerts/alt_5001/acknowledge \
  -H "Authorization: Bearer <access_token>"
```

**Response:** `200 OK`

```json
{
    "id": "alt_5001",
    "device_id": "dev_1003",
    "severity": "critical",
    "state": "acknowledged",
    "message": "Vibration 6.8 mm/s exceeds the 5.0 mm/s limit.",
    "raised_at": "2026-11-20T03:46:54.013778Z",
    "acknowledged_at": "2026-11-20T05:46:56.921265Z",
    "acknowledged_by": "demo-client"
}
```

**Error: already acknowledged**

```bash
curl -X POST http://localhost:8000/api/v1/alerts/alt_5001/acknowledge \
  -H "Authorization: Bearer <access_token>"
```

**Response:** `409 Conflict`

```json
{
    "error": {
        "code": "alert_already_acknowledged",
        "message": "This alert has already been acknowledged."
    }
}
```

**Error: alert not found**

```bash
curl -X POST http://localhost:8000/api/v1/alerts/alt_0000/acknowledge \
  -H "Authorization: Bearer <access_token>"
```

**Response:** `404 Not Found`

```json
{
    "error": {
        "code": "alert_not_found",
        "message": "No alert exists with the given ID."
    }
}
```

## Error codes

| Code | Status | Meaning |
|---|---|---|
| `unauthorized` | 401 | The token is missing, invalid or expired. |
| `invalid_credentials` | 401 | The client ID or client secret is incorrect. |
| `device_not_found` | 404 | No device exists with the given ID. |
| `alert_not_found` | 404 | No alert exists with the given ID. |
| `alert_already_acknowledged` | 409 | The alert was already acknowledged. |
| `validation_error` | 422 | The request contains invalid data. See `error.details`. |

## Test results

All 19 checks were run in sequence against one running instance. Python 3.13.18, FastAPI 0.163.2, API 1.2.0, tested on 2026-11-20.

| # | Scenario | Request | Expected | Actual | Result |
|---|---|---|---|---|---|
| 1 | Check service health without a token | `GET /api/v1/health` | 200 | 200 | Pass |
| 2 | Get an access token | `POST /api/v1/auth/token` | 200 | 200 | Pass |
| 3 | Request a token with a wrong secret | `POST /api/v1/auth/token` | 401 | 401 | Pass |
| 4 | List devices without a token | `GET /api/v1/devices` | 401 | 401 | Pass |
| 5 | List online devices, two per page | `GET /api/v1/devices?status=online&limit=2` | 200 | 200 | Pass |
| 6 | Get one device | `GET /api/v1/devices/dev_1001` | 200 | 200 | Pass |
| 7 | Get a device that does not exist | `GET /api/v1/devices/dev_9999` | 404 | 404 | Pass |
| 8 | Register a device | `POST /api/v1/devices` | 201 | 201 | Pass |
| 9 | Register a device with invalid data | `POST /api/v1/devices` | 422 | 422 | Pass |
| 10 | Move the new device to maintenance | `PATCH /api/v1/devices/dev_1006` | 200 | 200 | Pass |
| 11 | Delete the new device | `DELETE /api/v1/devices/dev_1006` | 204 | 204 | Pass |
| 12 | List the two latest readings | `GET /api/v1/devices/dev_1001/telemetry?limit=2` | 200 | 200 | Pass |
| 13 | Submit a normal reading to an offline device | `POST /api/v1/devices/dev_1005/telemetry` | 201 | 201 | Pass |
| 14 | Confirm the device is now online | `GET /api/v1/devices/dev_1005` | 200 | 200 | Pass |
| 15 | Submit a reading above the vibration limit | `POST /api/v1/devices/dev_1001/telemetry` | 201 | 201 | Pass |
| 16 | List open critical alerts | `GET /api/v1/alerts?severity=critical&state=open` | 200 | 200 | Pass |
| 17 | Acknowledge an alert | `POST /api/v1/alerts/alt_5001/acknowledge` | 200 | 200 | Pass |
| 18 | Acknowledge the same alert again | `POST /api/v1/alerts/alt_5001/acknowledge` | 409 | 409 | Pass |
| 19 | Acknowledge an alert that does not exist | `POST /api/v1/alerts/alt_0000/acknowledge` | 404 | 404 | Pass |

The raw JSON responses are stored in the repository folder [`docs/api/examples/`](https://github.com/rpattanaik04/edgepulse-docs/tree/main/docs/api/examples). To repeat the test, see the instructions in [`scripts/build_api_reference.py`](https://github.com/rpattanaik04/edgepulse-docs/blob/main/scripts/build_api_reference.py).

## Related information

- [Product overview](../overview/index.md)
- [OpenAPI specification (YAML)](openapi.yaml)
- [Documentation style guide](../contributing/style-guide.md)
