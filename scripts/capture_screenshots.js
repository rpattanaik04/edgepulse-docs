/**
 * Capture documentation screenshots from the running EdgePulse demo API.
 *
 * It drives the real dashboard and the real Swagger UI, so every screenshot shows
 * actual behavior. Access tokens are replaced with <access_token> before capture.
 *
 * Usage (from the repository root, with the API running on port 8000):
 *   npm install playwright          # once
 *   node scripts/capture_screenshots.js
 *
 * Optional environment variables:
 *   BASE_URL          API address. Default http://localhost:8000
 *   OUT_DIR           Output folder. Default docs/assets/screenshots
 *   SWAGGER_UI_DIST   Local swagger-ui-dist folder. Use it when the CDN is unreachable.
 *
 * Start the API with fresh data before each run, because the script changes data.
 */
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE_URL = (process.env.BASE_URL || "http://localhost:8000").replace(/\/$/, "");
const OUT_DIR = path.resolve(process.env.OUT_DIR || path.join(__dirname, "..", "docs", "assets", "screenshots"));
const SWAGGER_DIST = process.env.SWAGGER_UI_DIST;
const TYPES = { ".js": "application/javascript", ".css": "text/css" };

const shot = async (target, name) => {
  await target.screenshot({ path: path.join(OUT_DIR, name) });
  console.log("saved", name);
};

async function maskToken(page, token) {
  await page.evaluate((t) => {
    for (const n of document.querySelectorAll("pre, code, input, textarea")) {
      if ("value" in n && n.value && n.value.includes(t)) n.value = n.value.split(t).join("<access_token>");
      else if (n.textContent.includes(t)) n.textContent = n.textContent.split(t).join("<access_token>");
    }
  }, token);
}

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 2 });
  await context.route(/fastapi\.tiangolo\.com/, (r) => r.abort());
  if (SWAGGER_DIST) {
    await context.route(/cdn\.jsdelivr\.net\/npm\/swagger-ui-dist@5\//, (route) => {
      const file = route.request().url().split("/").pop();
      route.fulfill({ path: path.join(SWAGGER_DIST, file), contentType: TYPES[path.extname(file)] });
    });
  }
  const page = await context.newPage();
  const problems = [];
  page.on("pageerror", (e) => problems.push("pageerror: " + e.message));
  page.on("console", (m) => { if (m.type() === "error" && !/Failed to load resource/.test(m.text())) problems.push("console: " + m.text()); });

  // ---------- Swagger UI ----------
  await page.goto(BASE_URL + "/docs");
  await page.locator(".swagger-ui .info").waitFor();
  await page.waitForTimeout(500);
  await shot(page, "swagger-ui-overview.png");

  const tokenOp = page.locator("#operations-Authentication-create_token_api_v1_auth_token_post");
  await tokenOp.locator(".opblock-summary-control").click();
  await tokenOp.getByRole("button", { name: "Try it out" }).click();
  await tokenOp.getByRole("button", { name: "Execute" }).click();
  await tokenOp.locator(".live-responses-table").waitFor();
  const body = await tokenOp.locator(".live-responses-table .response-col_description pre").first().innerText();
  const token = JSON.parse(body).access_token;
  await maskToken(page, token);
  await shot(tokenOp, "swagger-ui-token-response.png");

  await page.getByRole("button", { name: "Authorize" }).first().click();
  await page.locator(".auth-container input").fill(token);
  await page.getByRole("button", { name: "Apply credentials" }).click();
  await page.locator(".modal-ux").waitFor();
  await maskToken(page, token);
  await shot(page.locator(".modal-ux"), "swagger-ui-authorized.png");
  await page.locator(".btn-done").click();

  await tokenOp.locator(".opblock-summary-control").click(); // collapse
  const listOp = page.locator("#operations-Devices-list_devices_api_v1_devices_get");
  await listOp.locator(".opblock-summary-control").click();
  await listOp.getByRole("button", { name: "Try it out" }).click();
  await listOp.locator('tr[data-param-name="limit"] input').fill("2");
  await listOp.getByRole("button", { name: "Execute" }).click();
  await listOp.locator(".live-responses-table").waitFor();
  await page.waitForTimeout(300);
  await maskToken(page, token);
  await shot(listOp, "swagger-ui-list-devices.png");


  // ---------- Dashboard ----------
  await page.goto(BASE_URL + "/dashboard");
  await page.getByRole("heading", { name: "Sign in" }).waitFor();
  await shot(page, "dashboard-sign-in.png");

  await page.getByRole("button", { name: "Sign in" }).click();
  await page.getByRole("heading", { name: "Overview" }).waitFor();
  await page.getByRole("row", { name: /Turbine Monitor 03/ }).waitFor();
  await shot(page, "dashboard-overview.png");

  await page.getByRole("row", { name: /Turbine Monitor 03/ }).click();
  await page.getByRole("heading", { name: "Device details: Turbine Monitor 03" }).waitFor();
  await shot(page.locator('section[aria-labelledby="det-h"]'), "dashboard-device-details.png");

  await shot(page.locator('section[aria-labelledby="alt-h"]'), "dashboard-alerts.png");
  await page.getByRole("row").filter({ hasText: "Vibration 6.8" }).getByRole("button", { name: "Acknowledge" }).click();
  await page.getByText("Alert alt_5001 acknowledged.").waitFor();
  await shot(page.locator("main"), "dashboard-alert-acknowledged.png");

  await page.getByRole("button", { name: "Add device" }).click();
  await page.getByLabel("Name").fill("x");
  await page.getByLabel("Site").fill("P");
  await page.getByRole("button", { name: "Register" }).click();
  await page.getByRole("alert").filter({ hasText: "invalid data" }).waitFor();
  await shot(page.locator("form").filter({ has: page.getByRole("heading", { name: "Add device" }) }), "dashboard-add-device-error.png");

  await page.getByLabel("Name").fill("Chiller Gateway 06");
  await page.getByLabel("Site").fill("Pune Plant");
  await page.getByRole("button", { name: "Register" }).click();
  await page.getByText("Registered Chiller Gateway 06").waitFor();
  await page.evaluate(() => window.scrollTo(0, 0));
  await shot(page, "dashboard-device-registered.png");

  await browser.close();
  if (problems.length) {
    console.error("Browser problems:\n" + problems.join("\n"));
    process.exit(1);
  }
  console.log("Done. No browser errors.");
})().catch((e) => { console.error(e); process.exit(1); });
