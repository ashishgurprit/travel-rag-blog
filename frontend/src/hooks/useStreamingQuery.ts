"use client"
import { useState, useCallback } from "react"

interface Source {
  title: string
  url: string
  source_type: string
  timestamp_seconds: number
}

interface Affiliate {
  program: string
  url: string
  cta: string
}

interface StreamingQueryState {
  query: string
  setQuery: (q: string) => void
  answer: string
  sources: Source[]
  affiliate: Affiliate | null
  disclosure: string
  isStreaming: boolean
  error: string
  submitQuery: (query: string) => void
}

interface SSEEvent {
  type: "text" | "sources" | "affiliate" | "disclosure"
  content: string | Source[] | Affiliate
}

export function useStreamingQuery(): StreamingQueryState {
  const [query, setQuery] = useState("")
  const [answer, setAnswer] = useState("")
  const [sources, setSources] = useState<Source[]>([])
  const [affiliate, setAffiliate] = useState<Affiliate | null>(null)
  const [disclosure, setDisclosure] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState("")

  const submitQuery = useCallback(async (q: string) => {
    // Reset state
    setAnswer("")
    setSources([])
    setAffiliate(null)
    setDisclosure("")
    setError("")
    setIsStreaming(true)
    setQuery(q)

    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({ query: q }),
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status} ${response.statusText}`)
      }

      if (!response.body) {
        throw new Error("No response body")
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Process complete lines
        const lines = buffer.split("\n")
        // Keep the last potentially incomplete line in the buffer
        buffer = lines.pop() ?? ""

        for (const line of lines) {
          const trimmed = line.trim()

          // SSE data lines start with "data: "
          if (!trimmed.startsWith("data:")) continue

          const jsonStr = trimmed.slice("data:".length).trim()
          if (!jsonStr || jsonStr === "[DONE]") continue

          let event: SSEEvent
          try {
            event = JSON.parse(jsonStr) as SSEEvent
          } catch {
            // Skip malformed JSON
            continue
          }

          switch (event.type) {
            case "text":
              setAnswer((prev) => prev + (event.content as string))
              break
            case "sources":
              setSources(event.content as Source[])
              break
            case "affiliate":
              setAffiliate(event.content as Affiliate)
              break
            case "disclosure":
              setDisclosure(event.content as string)
              setIsStreaming(false)
              break
          }
        }
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "An unexpected error occurred"
      setError(message)
    } finally {
      setIsStreaming(false)
    }
  }, [])

  return {
    query,
    setQuery,
    answer,
    sources,
    affiliate,
    disclosure,
    isStreaming,
    error,
    submitQuery,
  }
}
