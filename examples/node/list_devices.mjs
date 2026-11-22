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
