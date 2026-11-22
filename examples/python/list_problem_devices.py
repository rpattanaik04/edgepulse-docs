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
