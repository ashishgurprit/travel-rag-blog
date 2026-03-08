"use client"
import { ChatInput } from "@/components/ChatInput"
import { StreamedAnswer } from "@/components/StreamedAnswer"
import { SourceCard } from "@/components/SourceCard"
import { AffiliateLink } from "@/components/AffiliateLink"
import { useStreamingQuery } from "@/hooks/useStreamingQuery"

export default function Home() {
  const { answer, sources, affiliate, disclosure, isStreaming, error, submitQuery } = useStreamingQuery()
  return (
    <main className="min-h-screen bg-gray-50 flex flex-col items-center p-8">
      <h1 className="text-3xl font-bold mb-8 text-gray-900">Travel Search</h1>
      <div className="w-full max-w-2xl space-y-6">
        <ChatInput onSubmit={submitQuery} disabled={isStreaming} />
        {error && <p className="text-red-600">{error}</p>}
        {(answer || isStreaming) && <StreamedAnswer text={answer} isStreaming={isStreaming} />}
        {sources.length > 0 && (
          <div className="space-y-2">
            <h2 className="font-semibold text-gray-700">Sources</h2>
            {sources.map((s, i) => <SourceCard key={i} source={s} />)}
          </div>
        )}
        {affiliate && <AffiliateLink affiliate={affiliate} />}
        {disclosure && <p className="text-xs text-gray-400 mt-4">{disclosure}</p>}
      </div>
    </main>
  )
}
