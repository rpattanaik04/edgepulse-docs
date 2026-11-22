import requests

BASE_URL = "http://localhost:8000"

response = requests.post(
    f"{BASE_URL}/api/v1/auth/token",
    json={"client_id": "demo-client", "client_secret": "demo-secret"},
    timeout=90,
)
response.raise_for_status()
token = response.json()

print("Token type:", token["token_type"])
print("Expires in:", token["expires_in"], "seconds")

devices = requests.get(
    f"{BASE_URL}/api/v1/devices",
    headers={"Authorization": f"Bearer {token['access_token']}"},
    timeout=90,
)
print("Devices request status:", devices.status_code)
print("Devices returned:", devices.json()["total"])
