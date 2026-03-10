import { test, expect } from "@playwright/test"

/**
 * API contract tests — validate the SSE event schema produced by the backend
 * matches what the frontend's useStreamingQuery hook expects.
 *
 * These tests do NOT require the real backend. They use route mocking to
 * assert that the frontend handles every possible SSE event type correctly.
 *
 * Schema under test (backend/api/ask.py → frontend/src/hooks/useStreamingQuery.ts):
 *   text:        { type: "text",       content: string }
 *   sources:     { type: "sources",    content: Source[] }
 *   affiliate:   { type: "affiliate",  content: Affiliate }
 *   disclosure:  { type: "disclosure", content: string }
 */

// ---------------------------------------------------------------------------
// Shared SSE event builders
// ---------------------------------------------------------------------------

function sseEvent(type: string, content: unknown): string {
  return `data: ${JSON.stringify({ type, content })}\n\n`
}

const SOURCE = { title: "Test Source", url: "https://example.com", source_type: "web", timestamp_seconds: 0 }
const AFFILIATE = { program: "booking", url: "https://www.booking.com/?aid=test", cta: "Find hotels" }

// ---------------------------------------------------------------------------
// Contract: text event
// ---------------------------------------------------------------------------

test("contract: text event content is appended to answer", async ({ page }) => {
  await page.route("**/api/ask", async (route) => {
    await route.fulfill({
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
      body: [
        sseEvent("text", "Hello "),
        sseEvent("text", "world"),
        sseEvent("disclosure", "Disclaimer"),
      ].join(""),
    })
  })

  await page.goto("/")
  await page.getByPlaceholder("Ask about any travel destination...").fill("test")
  await page.getByRole("button", { name: "Search" }).click()

  // Both text tokens should be concatenated in the answer area
  await expect(page.getByText("Hello world")).toBeVisible()
})

// ---------------------------------------------------------------------------
// Contract: sources event
// ---------------------------------------------------------------------------

test("contract: sources event renders source cards", async ({ page }) => {
  await page.route("**/api/ask", async (route) => {
    await route.fulfill({
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
      body: [
        sseEvent("text", "Answer text"),
        sseEvent("sources", [SOURCE]),
        sseEvent("disclosure", "Disclaimer"),
      ].join(""),
    })
  })

  await page.goto("/")
  await page.getByPlaceholder("Ask about any travel destination...").fill("test")
  await page.getByRole("button", { name: "Search" }).click()

  await expect(page.getByText("Test Source")).toBeVisible()
  await expect(page.getByRole("link", { name: "Test Source" })).toHaveAttribute("href", "https://example.com")
})

test("contract: empty sources array renders no source cards", async ({ page }) => {
  await page.route("**/api/ask", async (route) => {
    await route.fulfill({
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
      body: [
        sseEvent("text", "Answer"),
        sseEvent("sources", []),
        sseEvent("disclosure", "Disclaimer"),
      ].join(""),
    })
  })

  await page.goto("/")
  await page.getByPlaceholder("Ask about any travel destination...").fill("test")
  await page.getByRole("button", { name: "Search" }).click()

  // Sources heading should NOT appear when list is empty
  await expect(page.getByRole("heading", { name: "Sources" })).not.toBeVisible()
})

// ---------------------------------------------------------------------------
// Contract: affiliate event
// ---------------------------------------------------------------------------

test("contract: affiliate event renders affiliate link with cta", async ({ page }) => {
  await page.route("**/api/ask", async (route) => {
    await route.fulfill({
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
      body: [
        sseEvent("text", "Book a hotel"),
        sseEvent("sources", []),
        sseEvent("affiliate", AFFILIATE),
        sseEvent("disclosure", "Disclaimer"),
      ].join(""),
    })
  })

  await page.goto("/")
  await page.getByPlaceholder("Ask about any travel destination...").fill("test")
  await page.getByRole("button", { name: "Search" }).click()

  await expect(page.getByText("Find hotels")).toBeVisible()
  const link = page.getByRole("link", { name: "Find hotels" })
  await expect(link).toHaveAttribute("href", "https://www.booking.com/?aid=test")
})

// ---------------------------------------------------------------------------
// Contract: disclosure event
// ---------------------------------------------------------------------------

test("contract: disclosure event renders disclaimer text", async ({ page }) => {
  await page.route("**/api/ask", async (route) => {
    await route.fulfill({
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
      body: [
        sseEvent("text", "Answer"),
        sseEvent("disclosure", "This response may contain affiliate links."),
      ].join(""),
    })
  })

  await page.goto("/")
  await page.getByPlaceholder("Ask about any travel destination...").fill("test")
  await page.getByRole("button", { name: "Search" }).click()

  await expect(page.getByText("This response may contain affiliate links.")).toBeVisible()
})

// ---------------------------------------------------------------------------
// Contract: unknown event types are silently ignored
// ---------------------------------------------------------------------------

test("contract: unknown event type does not crash the page", async ({ page }) => {
  await page.route("**/api/ask", async (route) => {
    await route.fulfill({
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
      body: [
        sseEvent("text", "Safe answer"),
        // unknown future event type
        sseEvent("metadata", { version: "v2" }),
        sseEvent("disclosure", "Disclaimer"),
      ].join(""),
    })
  })

  // Should not throw
  const errors: string[] = []
  page.on("pageerror", (err) => errors.push(err.message))

  await page.goto("/")
  await page.getByPlaceholder("Ask about any travel destination...").fill("test")
  await page.getByRole("button", { name: "Search" }).click()

  await expect(page.getByText("Safe answer")).toBeVisible()
  expect(errors).toHaveLength(0)
})

// ---------------------------------------------------------------------------
// Contract: malformed SSE line is silently skipped
// ---------------------------------------------------------------------------

test("contract: malformed JSON in SSE line is skipped gracefully", async ({ page }) => {
  await page.route("**/api/ask", async (route) => {
    await route.fulfill({
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
      body: [
        sseEvent("text", "Before bad line"),
        "data: {not valid json}\n\n",
        sseEvent("text", " after bad line"),
        sseEvent("disclosure", "Disclaimer"),
      ].join(""),
    })
  })

  const errors: string[] = []
  page.on("pageerror", (err) => errors.push(err.message))

  await page.goto("/")
  await page.getByPlaceholder("Ask about any travel destination...").fill("test")
  await page.getByRole("button", { name: "Search" }).click()

  // Both valid text tokens should appear
  await expect(page.getByText("Before bad line")).toBeVisible()
  await expect(page.getByText("after bad line")).toBeVisible()
  expect(errors).toHaveLength(0)
})
