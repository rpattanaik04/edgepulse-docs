const BASE_URL = "http://localhost:8000";

const tokenResponse = await fetch(`${BASE_URL}/api/v1/auth/token`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ client_id: "demo-client", client_secret: "demo-secret" }),
});
if (!tokenResponse.ok) {
  const { error } = await tokenResponse.json();
  throw new Error(`${tokenResponse.status} ${error.code}: ${error.message}`);
}
const token = await tokenResponse.json();
console.log("Token type:", token.token_type);
console.log("Expires in:", token.expires_in, "seconds");

const devices = await fetch(`${BASE_URL}/api/v1/devices`, {
  headers: { Authorization: `Bearer ${token.access_token}` },
});
console.log("Devices request status:", devices.status);
console.log("Devices returned:", (await devices.json()).total);
