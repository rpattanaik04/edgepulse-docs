# Release notes

Last updated: 2026-11-21

!!! note "Fictional history"
    EdgePulse is a fictional product. The dates and the history of versions 1.0.0 and 1.1.0 are invented for this portfolio. Version 1.2.0 matches the demo API in this repository.

**Audience:** Developers, administrators and operators.

## 1.2.0 — 2026-11-02

### Highlights

- All errors now use one consistent format.
- The API explains its own errors more clearly in the OpenAPI specification.

### Changes that need your action

!!! warning "Breaking change"
    Error responses changed from `{"detail": "..."}` to the `error` object. If your code reads `detail`, update it. See the [Upgrade guide](../migration/upgrade-1.1-to-1.2.md).

### Improvements

- The response format is the same for every error: `error.code` and `error.message`, plus `error.details` for validation errors.
- Validation errors list each field in `error.details`.
- The `/health` response uses a UTC timestamp that ends in `Z`.
- The OpenAPI specification documents the real error responses.
- The dashboard is included in the demo server.

### Fixes

- The OpenAPI specification showed the wrong error code for a 401 response.

## 1.1.0 — 2026-09-14

### New features

- Alerts, with the states `open` and `acknowledged`.
- Automatic critical alert for vibration above 5.0 mm/s.
- Acknowledge an alert with `POST /alerts/{id}/acknowledge`.

### Improvements

- Device lists support the `status`, `site`, `limit` and `offset` parameters.

## 1.0.0 — 2026-07-06

### Initial release

- Token authentication.
- Device registration and management.
- Telemetry readings: temperature, vibration and pressure.

## Known limitations

- Data is stored in memory and resets on restart.
- There is one set of client credentials.
- The vibration limit is not configurable.

## Related information

- [Upgrade guide: 1.1 to 1.2](../migration/upgrade-1.1-to-1.2.md)
- [API reference](../api/reference.md)
