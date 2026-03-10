import { defineConfig, devices } from "@playwright/test"

/**
 * Playwright E2E config for the Travel RAG frontend.
 *
 * Test modes:
 *   - Against the running Next.js dev server (CI): starts `next start` on 3000
 *   - Against a live backend stub (api-contract tests): expects mock server on 3001
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",

  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  // Start Next.js production server before tests (if NEXT_START=1 is set)
  webServer: process.env.NEXT_START
    ? {
        command: "pnpm start",
        url: "http://localhost:3000",
        reuseExistingServer: !process.env.CI,
        timeout: 60_000,
      }
    : undefined,
})
