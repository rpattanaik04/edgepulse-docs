# MQTT integration guide

Last updated: 2026-11-21

## Overview

Many industrial devices publish readings over MQTT, a lightweight messaging protocol. The EdgePulse API accepts readings over REST only. This guide shows how to connect the two with a small bridge script. The bridge listens for MQTT messages and forwards each one to the API.

**Audience:** Developers and integration engineers.

## Purpose

After you complete this guide, readings that a device publishes to an MQTT broker appear in EdgePulse. The platform raises alerts for them as usual.

## Prerequisites

- A running EdgePulse API. See the [Installation guide](../installation/index.md).
- Python 3.10 or later.
- An MQTT broker that you can reach. This guide uses a local broker on port 1883.
- The example files in `examples/python/`.

## Key concepts

- **Broker.** A server that receives MQTT messages and delivers them to subscribers.
- **Topic.** The address of a message. The bridge uses `edgepulse/devices/<device_id>/telemetry`.
- **Subscriber.** A client that receives messages from topics. The bridge is a subscriber.

!!! note "Data flow"
    Device → MQTT broker → bridge → EdgePulse REST API → alert rule.

## Message format

Publish one JSON object per message to the topic of the device. All three fields are required.

```json
{"temperature_c": 74.3, "vibration_mm_s": 6.1, "pressure_kpa": 411.0}
```

The topic filter is `edgepulse/devices/+/telemetry`. The `+` matches one device ID.

## Procedure

1. Install the Python packages.

    ```bash
    pip install requests paho-mqtt
    ```

2. Start the EdgePulse API. Keep it running.

3. Set the broker address if the broker is not on `localhost:1883`.

    ```bash
    export MQTT_HOST=broker.example.com
    export MQTT_PORT=1883
    ```

4. Start the bridge.

    ```bash
    cd examples/python
    python mqtt_bridge.py
    ```

5. Publish a test message. This example uses the Python client.

    ```python
    import json
    import paho.mqtt.client as mqtt

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect("localhost", 1883)
    client.loop_start()
    reading = {"temperature_c": 74.3, "vibration_mm_s": 6.1, "pressure_kpa": 411.0}
    client.publish("edgepulse/devices/dev_1005/telemetry", json.dumps(reading), qos=1).wait_for_publish()
    client.loop_stop()
    ```

## Expected results

The bridge prints one line for each message:

```text
Connected to the broker (Success). Subscribing to edgepulse/devices/+/telemetry
forwarded: dev_1005
```

The reading above has a vibration value of 6.1 mm/s, which is above the 5.0 mm/s limit. Check for the new critical alert:

```bash
curl "http://localhost:8000/api/v1/alerts?device_id=dev_1005&severity=critical" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "items": [
    {
      "id": "alt_5004",
      "device_id": "dev_1005",
      "severity": "critical",
      "state": "open",
      "message": "Vibration 6.1 mm/s exceeds the 5.0 mm/s limit.",
      "raised_at": "2026-11-21T12:15:53.739964Z",
      "acknowledged_at": null,
      "acknowledged_by": null
    }
  ],
  "total": 1
}
```

Your `id` and `raised_at` values differ.

!!! note "Test record"
    This output comes from a test on 2026-11-21 with a local broker and the demo API v1.2.0.

## Bridge script

The complete script is below. It is the tested file `examples/python/mqtt_bridge.py`.

```python
"""Forward MQTT telemetry messages to the EdgePulse REST API.

Topic format:   edgepulse/devices/<device_id>/telemetry
Payload format: {"temperature_c": 72.4, "vibration_mm_s": 2.1, "pressure_kpa": 412.0}

Environment variables:
    MQTT_HOST (default localhost), MQTT_PORT (default 1883),
    plus the variables that edgepulse_client.py reads.
"""

import json
import os
import re

import paho.mqtt.client as mqtt

from edgepulse_client import EdgePulseClient, EdgePulseError

TOPIC_FILTER = "edgepulse/devices/+/telemetry"
TOPIC_PATTERN = re.compile(r"^edgepulse/devices/(?P<device_id>[^/]+)/telemetry$")
FIELDS = ("temperature_c", "vibration_mm_s", "pressure_kpa")


def forward(api, topic, payload):
    """Send one MQTT message to the API. Return a short result string."""
    match = TOPIC_PATTERN.match(topic)
    if not match:
        return f"skipped: unexpected topic {topic}"
    try:
        data = json.loads(payload)
        reading = {name: data[name] for name in FIELDS}
    except (ValueError, KeyError, TypeError):
        return f"skipped: invalid payload on {topic}"
    try:
        api.request("POST", f"/api/v1/devices/{match['device_id']}/telemetry", json=reading)
    except EdgePulseError as error:
        return f"rejected: {error.code} for {match['device_id']}"
    return f"forwarded: {match['device_id']}"


def main():
    api = EdgePulseClient()

    def on_connect(client, userdata, flags, reason_code, properties):
        print(f"Connected to the broker ({reason_code}). Subscribing to {TOPIC_FILTER}")
        client.subscribe(TOPIC_FILTER)

    def on_message(client, userdata, message):
        print(forward(api, message.topic, message.payload), flush=True)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(os.getenv("MQTT_HOST", "localhost"), int(os.getenv("MQTT_PORT", "1883")))
    client.loop_forever()


if __name__ == "__main__":
    main()
```

## Troubleshooting

| Message or symptom | Cause | Fix |
|---|---|---|
| `skipped: unexpected topic ...` | The topic does not match the filter. | Publish to `edgepulse/devices/<device_id>/telemetry`. |
| `skipped: invalid payload ...` | The payload is not JSON, or a field is missing. | Send all three fields as a JSON object. |
| `rejected: device_not_found ...` | The device ID is not registered. | Register the device first. See the [Administrator guide](../admin-guide/index.md). |
| `rejected: validation_error ...` | A value is outside the allowed range. | Check the ranges in the [API reference](../api/reference.md). |
| `ConnectionRefusedError` | The broker is not running or the address is wrong. | Start the broker and check `MQTT_HOST` and `MQTT_PORT`. |
| The first request is slow | A free-tier host is waking up. | Wait about one minute and retry. |

## Best practices

- Use QoS 1 so that the broker retries a message that was not delivered.
- Run the bridge as a service that restarts after a failure.
- Use a broker with authentication and TLS in production. The sample uses neither.
- Keep one topic per device. Do not put several devices in one message.

!!! warning "Limitations of the sample"
    The bridge does not buffer messages. If the API is unreachable, the reading is lost. It also has no TLS or broker login.

## Related information

- [Developer guide](../developer-guide/index.md)
- [API reference](../api/reference.md)
- [Troubleshooting guide](../troubleshooting/index.md)
