# EdgePulse API reference

- **Audience:** Developers and integrators who call the EdgePulse REST API.
- **Document type:** API reference
- **Applies to:** EdgePulse API {{API_VERSION}}
- **Last updated:** {{TESTED_ON}}
- **Tested on:** {{TESTED_ON}}, against a running instance of the API

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

{{req:health}}

**Response:** {{status:health}}

{{resp:health}}

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

{{req:token}}

**Response:** {{status:token}}

{{resp:token}}

| Field | Type | Description |
|---|---|---|
| `access_token` | string | The token to send with each request. |
| `token_type` | string | Always `Bearer`. |
| `expires_in` | integer | Lifetime in seconds. |

**Error: wrong credentials**

{{req:token-invalid}}

**Response:** {{status:token-invalid}}

{{resp:token-invalid}}

**Error: missing token on a protected endpoint**

{{req:devices-no-token}}

**Response:** {{status:devices-no-token}}

{{resp:devices-no-token}}

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

{{req:devices-list}}

**Response:** {{status:devices-list}}

{{resp:devices-list}}

`total` is the number of devices that match the filters, not the number on the page.

### Get a device

`GET /api/v1/devices/{device_id}`

**Request**

{{req:device-get}}

**Response:** {{status:device-get}}

{{resp:device-get}}

**Error: device not found**

{{req:device-not-found}}

**Response:** {{status:device-not-found}}

{{resp:device-not-found}}

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

{{req:device-create}}

**Response:** {{status:device-create}}

{{resp:device-create}}

**Error: invalid data**

{{req:device-create-invalid}}

**Response:** {{status:device-create-invalid}}

{{resp:device-create-invalid}}

### Update a device

`PATCH /api/v1/devices/{device_id}`

Changes only the fields you send. All fields are optional: `name`, `site`, `status`, `firmware`.

**Request**

{{req:device-update}}

**Response:** {{status:device-update}}

{{resp:device-update}}

### Delete a device

`DELETE /api/v1/devices/{device_id}`

Deletes the device together with its readings and alerts.

!!! warning
    Deletion cannot be undone.

**Request**

{{req:device-delete}}

**Response:** {{status:device-delete}}

{{resp:device-delete}}

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

{{req:telemetry-list}}

**Response:** {{status:telemetry-list}}

{{resp:telemetry-list}}

### Submit a telemetry reading

`POST /api/v1/devices/{device_id}/telemetry`

Stores one reading. The device `last_seen` time is updated, and an `offline` device becomes `online`.

!!! note "Automatic alert"
    If `vibration_mm_s` is greater than 5.0, the API raises a critical alert.

**Request body.** Send `temperature_c`, `vibration_mm_s` and `pressure_kpa`. `timestamp` is optional.

**Request**

{{req:telemetry-submit}}

**Response:** {{status:telemetry-submit}}

{{resp:telemetry-submit}}

**Result: the device is now online**

{{req:device-after-telemetry}}

**Response:** {{status:device-after-telemetry}}

{{resp:device-after-telemetry}}

**Example: a reading above the vibration limit**

{{req:telemetry-high-vibration}}

**Response:** {{status:telemetry-high-vibration}}

{{resp:telemetry-high-vibration}}

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

{{req:alerts-list}}

**Response:** {{status:alerts-list}}

{{resp:alerts-list}}

The first item is the alert raised by the high-vibration reading submitted earlier.

### Acknowledge an alert

`POST /api/v1/alerts/{alert_id}/acknowledge`

Marks an open alert as acknowledged and records who acknowledged it and when.

**Request**

{{req:alert-acknowledge}}

**Response:** {{status:alert-acknowledge}}

{{resp:alert-acknowledge}}

**Error: already acknowledged**

{{req:alert-acknowledge-again}}

**Response:** {{status:alert-acknowledge-again}}

{{resp:alert-acknowledge-again}}

**Error: alert not found**

{{req:alert-not-found}}

**Response:** {{status:alert-not-found}}

{{resp:alert-not-found}}

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

All {{TOTAL}} checks were run in sequence against one running instance. Python {{PYTHON}}, FastAPI {{FASTAPI}}, API {{API_VERSION}}, tested on {{TESTED_ON}}.

{{RESULTS_TABLE}}

The raw JSON responses are stored in the repository folder [`docs/api/examples/`](https://github.com/rpattanaik04/edgepulse-docs/tree/main/docs/api/examples). To repeat the test, see the instructions in [`scripts/build_api_reference.py`](https://github.com/rpattanaik04/edgepulse-docs/blob/main/scripts/build_api_reference.py).

## Related information

- [Product overview](../overview/index.md)
- [OpenAPI specification (YAML)](openapi.yaml)
- [Documentation style guide](../contributing/style-guide.md)
