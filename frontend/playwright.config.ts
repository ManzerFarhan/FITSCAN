import { defineConfig } from "@playwright/test";

// E2E (P4-13). Expects the backend on :8000 and the frontend on FRONTEND_URL (default :3000).
// Backend must allow the frontend origin: FRONTEND_ORIGIN=http://localhost:3000
export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  expect: { timeout: 60_000 },
  use: { baseURL: process.env.FRONTEND_URL ?? "http://localhost:3000", trace: "retain-on-failure" },
  reporter: [["list"]],
});
