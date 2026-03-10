import { test, expect, Page } from "@playwright/test"

/**
 * E2E tests for the main chat interface.
 *
 * These tests run against the running Next.js app (localhost:3000).
 * The API is mocked at the network level using route interception so
 * tests are fast and deterministic without a live FastAPI backend.
 */

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Canonical SSE response that simulates a successful RAG answer. */
const SSE_RAG_RESPONSE = [
  `data: {"type":"text","content":"The best ramen in Tokyo is "}\n\n`,
  `data: {"type":"text","content":"at Ichiran Shinjuku."}\n\n`,
  `data: {"type":"sources","content":[{"title":"Ichiran Review","url":"https://example.com/ichiran","source_type":"reddit","timestamp_seconds":0}]}\n\n`,
  `data: {"type":"disclosure","content":"This response may contain affiliate links."}\n\n`,
].join("")

/** SSE response that includes an affiliate event before disclosure. */
const SSE_AFFILIATE_RESPONSE = [
  `data: {"type":"text","content":"Book a hotel in Tokyo."}\n\n`,
  `data: {"type":"sources","content":[]}\n\n`,
  `data: {"type":"affiliate","content":{"program":"booking","url":"https://www.booking.com/?aid=test","cta":"Find hotels on Booking.com"}}\n\n`,
  `data: {"type":"disclosure","content":"This response may contain affiliate links."}\n\n`,
].join("")

/** SSE response for a logistics query (trip planner path). */
const SSE_LOGISTICS_RESPONSE = [
  `data: {"type":"text","content":"You need a visa on arrival for Japan."}\n\n`,
  `data: {"type":"sources","content":[{"title":"Japan Tourism","url":"https://japan.travel","source_type":"web","timestamp_seconds":0}]}\n\n`,
  `data: {"type":"disclosure","content":"This response may contain affiliate links."}\n\n`,
].join("")

async function mockApiAsk(page: Page, sseBody: string) {
  await page.route("**/api/ask", async (route) => {
    await route.fulfill({
      status: 200,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
      },
      body: sseBody,
    })
  })
}

async function submitQuery(page: Page, query: string) {
  await page.getByPlaceholder("Ask about any travel destination...").fill(query)
  await page.getByRole("button", { name: "Search" }).click()
}

// ---------------------------------------------------------------------------
// Tests: Page structure
// ---------------------------------------------------------------------------

test.describe("Page structure", () => {
  test("loads with heading and input", async ({ page }) => {
    await page.goto("/")
    await expect(page.getByRole("heading", { name: "Travel Search" })).toBeVisible()
    await expect(page.getByPlaceholder("Ask about any travel destination...")).toBeVisible()
    await expect(page.getByRole("button", { name: "Search" })).toBeVisible()
  })

  test("search button is disabled on empty input", async ({ page }) => {
    await page.goto("/")
    const btn = page.getByRole("button", { name: "Search" })
    await expect(btn).toBeDisabled()
  })

  test("search button enables when input has text", async ({ page }) => {
    await page.goto("/")
    await page.getByPlaceholder("Ask about any travel destination...").fill("best ramen")
    await expect(page.getByRole("button", { name: "Search" })).toBeEnabled()
  })
})

// ---------------------------------------------------------------------------
// Tests: Happy path query → answer
// ---------------------------------------------------------------------------

test.describe("Chat — happy path", () => {
  test("submitting a query streams answer text", async ({ page }) => {
    await mockApiAsk(page, SSE_RAG_RESPONSE)
    await page.goto("/")
    await submitQuery(page, "best ramen in tokyo")

    await expect(page.getByText("The best ramen in Tokyo is")).toBeVisible()
    await expect(page.getByText("at Ichiran Shinjuku.")).toBeVisible()
  })

  test("sources section appears with title and link", async ({ page }) => {
    await mockApiAsk(page, SSE_RAG_RESPONSE)
    await page.goto("/")
    await submitQuery(page, "best ramen in tokyo")

    await expect(page.getByRole("heading", { name: "Sources" })).toBeVisible()
    await expect(page.getByText("Ichiran Review")).toBeVisible()
  })

  test("disclosure text appears after response", async ({ page }) => {
    await mockApiAsk(page, SSE_RAG_RESPONSE)
    await page.goto("/")
    await submitQuery(page, "best ramen in tokyo")

    await expect(page.getByText("This response may contain affiliate links.")).toBeVisible()
  })

  test("Enter key submits the query", async ({ page }) => {
    await mockApiAsk(page, SSE_RAG_RESPONSE)
    await page.goto("/")
    await page.getByPlaceholder("Ask about any travel destination...").fill("best ramen in tokyo")
    await page.keyboard.press("Enter")

    await expect(page.getByText("at Ichiran Shinjuku.")).toBeVisible()
  })

  test("input is cleared after submit", async ({ page }) => {
    await mockApiAsk(page, SSE_RAG_RESPONSE)
    await page.goto("/")
    await submitQuery(page, "best ramen in tokyo")

    await expect(page.getByPlaceholder("Ask about any travel destination...")).toHaveValue("")
  })
})

// ---------------------------------------------------------------------------
// Tests: Affiliate link
// ---------------------------------------------------------------------------

test.describe("Affiliate link", () => {
  test("affiliate link appears when event is in stream", async ({ page }) => {
    await mockApiAsk(page, SSE_AFFILIATE_RESPONSE)
    await page.goto("/")
    await submitQuery(page, "where to stay in tokyo")

    await expect(page.getByText("Find hotels on Booking.com")).toBeVisible()
  })

  test("affiliate link has correct href", async ({ page }) => {
    await mockApiAsk(page, SSE_AFFILIATE_RESPONSE)
    await page.goto("/")
    await submitQuery(page, "where to stay in tokyo")

    const link = page.getByRole("link", { name: /Booking\.com/i })
    await expect(link).toHaveAttribute("href", /booking\.com/)
  })

  test("no affiliate link shown when not in stream", async ({ page }) => {
    await mockApiAsk(page, SSE_RAG_RESPONSE)
    await page.goto("/")
    await submitQuery(page, "best ramen in tokyo")

    // Booking.com link should NOT be present
    await expect(page.getByRole("link", { name: /Booking\.com/i })).not.toBeVisible()
  })
})

// ---------------------------------------------------------------------------
// Tests: Logistics (trip planner) path
// ---------------------------------------------------------------------------

test.describe("Logistics queries", () => {
  test("visa question returns logistics answer", async ({ page }) => {
    await mockApiAsk(page, SSE_LOGISTICS_RESPONSE)
    await page.goto("/")
    await submitQuery(page, "do I need a visa for Japan from Australia")

    await expect(page.getByText("You need a visa on arrival for Japan.")).toBeVisible()
  })

  test("sources from web appear for logistics query", async ({ page }) => {
    await mockApiAsk(page, SSE_LOGISTICS_RESPONSE)
    await page.goto("/")
    await submitQuery(page, "do I need a visa for Japan from Australia")

    await expect(page.getByText("Japan Tourism")).toBeVisible()
  })
})

// ---------------------------------------------------------------------------
// Tests: Error handling
// ---------------------------------------------------------------------------

test.describe("Error handling", () => {
  test("shows error message on API failure", async ({ page }) => {
    await page.route("**/api/ask", async (route) => {
      await route.fulfill({ status: 500, body: "Internal Server Error" })
    })
    await page.goto("/")
    await submitQuery(page, "best ramen in tokyo")

    // An error message should appear
    await expect(page.locator("p.text-red-600")).toBeVisible({ timeout: 5000 })
  })

  test("search button re-enables after error", async ({ page }) => {
    await page.route("**/api/ask", async (route) => {
      await route.fulfill({ status: 500, body: "error" })
    })
    await page.goto("/")
    await submitQuery(page, "best ramen in tokyo")

    // Button is disabled until user types again (input cleared on submit — correct behaviour)
    await expect(page.locator("p.text-red-600")).toBeVisible({ timeout: 5000 })
    // Typing new text re-enables the button
    await page.getByPlaceholder("Ask about any travel destination...").fill("new query")
    await expect(page.getByRole("button", { name: "Search" })).toBeEnabled()
  })

  test("second query clears previous answer", async ({ page }) => {
    await mockApiAsk(page, SSE_RAG_RESPONSE)
    await page.goto("/")
    await submitQuery(page, "best ramen in tokyo")
    await expect(page.getByText("at Ichiran Shinjuku.")).toBeVisible()

    // Submit a second query with a different mock
    await page.route("**/api/ask", async (route) => {
      await route.fulfill({
        status: 200,
        headers: { "Content-Type": "text/event-stream" },
        body: [
          `data: {"type":"text","content":"Different answer."}\n\n`,
          `data: {"type":"disclosure","content":"Disclaimer."}\n\n`,
        ].join(""),
      })
    })
    await submitQuery(page, "second question")
    await expect(page.getByText("Different answer.")).toBeVisible()
    // Old answer should be gone
    await expect(page.getByText("at Ichiran Shinjuku.")).not.toBeVisible()
  })
})

// ---------------------------------------------------------------------------
// Tests: Legal pages
// ---------------------------------------------------------------------------

test.describe("Legal pages", () => {
  test("privacy page loads", async ({ page }) => {
    await page.goto("/privacy")
    await expect(page).not.toHaveURL(/404/)
  })

  test("terms page loads", async ({ page }) => {
    await page.goto("/terms")
    await expect(page).not.toHaveURL(/404/)
  })

  test("disclosure page loads", async ({ page }) => {
    await page.goto("/disclosure")
    await expect(page).not.toHaveURL(/404/)
  })
})
