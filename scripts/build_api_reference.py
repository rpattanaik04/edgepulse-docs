"""Build the API reference from real, tested responses.

What it does
1. Calls a running EdgePulse API through a fixed test scenario.
2. Checks every status code against the expected value.
3. Saves each response body to docs/api/examples/.
4. Fills the placeholders in the template to create docs/api/reference.md.

Nothing in the generated JSON is typed by hand. If any check fails, no files are written.

Usage (from the repository root)
    cd api-demo && uvicorn app.main:app --port 8000      # terminal 1
    python scripts/build_api_reference.py                # terminal 2
Optional: set BASE_URL to test a hosted copy of the API.
"""

import http
import json
import os
import platform
import re
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "scripts" / "templates" / "api-reference.template.md"
OUTPUT = ROOT / "docs" / "api" / "reference.md"
EXAMPLES = ROOT / "docs" / "api" / "examples"

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
DOC_BASE_URL = "http://localhost:8000"  # URL shown in the documentation
TOKEN_PLACEHOLDER = "<access_token>"

# key, scenario, method, path, body, needs token, expected status
STEPS = [
    ("health", "Check service health without a token", "GET", "/api/v1/health", None, False, 200),
    ("token", "Get an access token", "POST", "/api/v1/auth/token",
     {"client_id": "demo-client", "client_secret": "demo-secret"}, False, 200),
    ("token-invalid", "Request a token with a wrong secret", "POST", "/api/v1/auth/token",
     {"client_id": "demo-client", "client_secret": "wrong-secret"}, False, 401),
    ("devices-no-token", "List devices without a token", "GET", "/api/v1/devices", None, False, 401),
    ("devices-list", "List online devices, two per page", "GET",
     "/api/v1/devices?status=online&limit=2", None, True, 200),
    ("device-get", "Get one device", "GET", "/api/v1/devices/dev_1001", None, True, 200),
    ("device-not-found", "Get a device that does not exist", "GET", "/api/v1/devices/dev_9999",
     None, True, 404),
    ("device-create", "Register a device", "POST", "/api/v1/devices",
     {"name": "Chiller Gateway 06", "site": "Pune Plant", "protocol": "mqtt", "firmware": "1.2.4"},
     True, 201),
    ("device-create-invalid", "Register a device with invalid data", "POST", "/api/v1/devices",
     {"name": "x", "site": "P"}, True, 422),
    ("device-update", "Move the new device to maintenance", "PATCH", "/api/v1/devices/{new_id}",
     {"status": "maintenance"}, True, 200),
    ("device-delete", "Delete the new device", "DELETE", "/api/v1/devices/{new_id}", None, True, 204),
    ("telemetry-list", "List the two latest readings", "GET",
     "/api/v1/devices/dev_1001/telemetry?limit=2", None, True, 200),
    ("telemetry-submit", "Submit a normal reading to an offline device", "POST",
     "/api/v1/devices/dev_1005/telemetry",
     {"temperature_c": 71.5, "vibration_mm_s": 2.3, "pressure_kpa": 405.0}, True, 201),
    ("device-after-telemetry", "Confirm the device is now online", "GET",
     "/api/v1/devices/dev_1005", None, True, 200),
    ("telemetry-high-vibration", "Submit a reading above the vibration limit", "POST",
     "/api/v1/devices/dev_1001/telemetry",
     {"temperature_c": 78.2, "vibration_mm_s": 6.4, "pressure_kpa": 421.0}, True, 201),
    ("alerts-list", "List open critical alerts", "GET",
     "/api/v1/alerts?severity=critical&state=open", None, True, 200),
    ("alert-acknowledge", "Acknowledge an alert", "POST", "/api/v1/alerts/alt_5001/acknowledge",
     None, True, 200),
    ("alert-acknowledge-again", "Acknowledge the same alert again", "POST",
     "/api/v1/alerts/alt_5001/acknowledge", None, True, 409),
    ("alert-not-found", "Acknowledge an alert that does not exist", "POST",
     "/api/v1/alerts/alt_0000/acknowledge", None, True, 404),
]


def pretty(data) -> str:
    return json.dumps(data, indent=4, ensure_ascii=False)


def curl_command(method: str, path: str, body, needs_token: bool) -> str:
    url = f"{DOC_BASE_URL}{path}"
    if "?" in path:
        url = f'"{url}"'  # quote the URL so the shell does not treat & as a background operator
    lines = [f"curl -X {method} {url}" if method != "GET" else f"curl {url}"]
    if needs_token:
        lines.append(f'-H "Authorization: Bearer {TOKEN_PLACEHOLDER}"')
    if body is not None:
        lines.append('-H "Content-Type: application/json"')
        indented = json.dumps(body, indent=2, ensure_ascii=False).replace("\n", "\n  ")
        lines.append(f"-d '{indented}'")
    return " \\\n  ".join(lines)


def status_text(code: int) -> str:
    return f"{code} {http.HTTPStatus(code).phrase}"


def run_scenario() -> list[dict]:
    results, ctx, token = [], {}, None
    with httpx.Client(base_url=BASE_URL, timeout=15) as client:
        for key, scenario, method, path, body, needs_token, expected in STEPS:
            real_path = path.format(**ctx)
            headers = {"Authorization": f"Bearer {token}"} if needs_token and token else {}
            resp = client.request(method, real_path, json=body, headers=headers)
            data = resp.json() if resp.content else None
            if key == "token":
                token = data["access_token"]
            if key == "device-create":
                ctx["new_id"] = data["id"]
            # The documentation shows a placeholder, never a real token.
            shown = json.loads(json.dumps(data).replace(token, TOKEN_PLACEHOLDER)) if (
                token and data is not None) else data
            results.append({
                "key": key, "scenario": scenario, "method": method,
                "path": path.format(new_id=ctx.get("new_id", "")),
                "body": body, "needs_token": needs_token,
                "expected": expected, "actual": resp.status_code, "data": shown,
            })
    return results


def render(results: list[dict]) -> str:
    by_key = {r["key"]: r for r in results}
    text = TEMPLATE.read_text(encoding="utf-8")

    def sub(match: re.Match) -> str:
        kind, key = match.group(1), match.group(2)
        r = by_key[key]
        if kind == "req":
            return "```bash\n" + curl_command(r["method"], r["path"], r["body"], r["needs_token"]) + "\n```"
        if kind == "resp":
            if r["data"] is None:
                return "The response has no body."
            return "```json\n" + pretty(r["data"]) + "\n```"
        if kind == "status":
            return f"`{status_text(r['actual'])}`"
        raise KeyError(kind)

    text = re.sub(r"\{\{(req|resp|status):([a-z0-9-]+)\}\}", sub, text)

    rows = ["| # | Scenario | Request | Expected | Actual | Result |", "|---|---|---|---|---|---|"]
    for i, r in enumerate(results, 1):
        rows.append(
            f"| {i} | {r['scenario']} | `{r['method']} {r['path']}` | {r['expected']} | "
            f"{r['actual']} | {'Pass' if r['expected'] == r['actual'] else 'FAIL'} |"
        )
    health = by_key["health"]["data"]
    meta = {
        "RESULTS_TABLE": "\n".join(rows),
        "TESTED_ON": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "API_VERSION": health["version"],
        "PYTHON": platform.python_version(),
        "FASTAPI": version("fastapi"),
        "TOTAL": str(len(results)),
    }
    for name, value in meta.items():
        text = text.replace("{{" + name + "}}", value)
    leftover = re.findall(r"\{\{[^}]+\}\}", text)
    if leftover:
        raise SystemExit(f"Unfilled placeholders in template: {leftover}")
    return text


def main() -> None:
    results = run_scenario()
    failures = [r for r in results if r["expected"] != r["actual"]]
    for r in results:
        mark = "ok  " if r["expected"] == r["actual"] else "FAIL"
        print(f"{mark} {r['method']:6} {r['path']:55} expected {r['expected']} got {r['actual']}")
    if failures:
        raise SystemExit(f"{len(failures)} check(s) failed. No files written.")

    EXAMPLES.mkdir(parents=True, exist_ok=True)
    for old in EXAMPLES.glob("*.json"):
        old.unlink()
    for i, r in enumerate(results, 1):
        if r["data"] is not None:
            (EXAMPLES / f"{i:02d}-{r['key']}.json").write_text(pretty(r["data"]) + "\n", encoding="utf-8")
    OUTPUT.write_text(render(results), encoding="utf-8")
    print(f"\nAll {len(results)} checks passed. Wrote {OUTPUT.relative_to(ROOT)} and "
          f"{len(list(EXAMPLES.glob('*.json')))} example files.")


if __name__ == "__main__":
    sys.exit(main())
