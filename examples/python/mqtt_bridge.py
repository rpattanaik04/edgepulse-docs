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
